"""
分层：
  第 1 层   加载与注册    FileSkillStore（SKILL.md/meta.json 的解析、渲染与原子写入，不含内存索引或可见性规则）、SkillRegistry（内存索引）
  第 1.5 层 导入         SkillImporter（zip -> 校验 -> 规范化 -> 安装），"宽进严出"：加载器只认内部标准格式
  第 2 层   提供给 LLM    SkillToolkit（目录快照、read_skill、read_skill_resource）
  第 3 层   提供给 Harness SkillAdminService（增删改查、导入、启停、校验、审计）

磁盘布局：
  内置库  src/skills/<group>/<name>/...                  只读，skill_id 如 jenkins/build-failure-triage
  团队库 <data>/skills/<group>/<name>
  每个包： SKILL.md（frontmatter: name/description + 正文）、meta.json（Harness 字段，模型读不到）、其余 = 资源

依赖：核心逻辑只用标准库和 pydantic；PyYAML 仅在导入 zip 时才需要（延迟导入）。
"""
import os
import re
import json
import shutil
import tempfile
from pathlib import Path

from model.errors import SkillReadOnly
from model.errors import SkillInvalid, SkillNotFound,SkillError
from datetime import datetime, timezone
from typing import Any, Literal, Mapping
from skills.models import SkillDetail


_SKILL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*(?:/[a-z0-9][a-z0-9_-]*)*$")
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")  # 与 Agent Skills 规范的 name 规则一致
_RESERVED_FILES = {"SKILL.md", "meta.json"}  # 包内保留文件：不算资源，模型不可读
_BAD_PATH_CHARS = re.compile(r'[<>:"|?*\x00-\x1f]')
_BLOCK_SCALAR_RE = re.compile(r"[>|][+-]?\d?[+-]?")
_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
_TOOL_TOKEN_RE = re.compile(r"[^\s()]+(?:\([^)]*\))?")

# --------------------------------------------------------------------------- #
# 通用小工具
# --------------------------------------------------------------------------- #


def check_skill_id(skill_id: str) -> str:
    if len(skill_id) > 100 or not _SKILL_ID_RE.fullmatch(skill_id):
        raise SkillInvalid(f"非法 skill_id: {skill_id!r}（只允许小写字母、数字、-、_，用 / 分层）")
    return skill_id


def check_slug(slug: str) -> str:
    if len(slug) > 64 or not _SLUG_RE.fullmatch(slug):
        raise SkillInvalid(f"非法 slug: {slug!r}（小写字母、数字、单个连字符，最长 64）")
    return slug

"""先写临时文件再替换，避免写一半崩溃留下损坏文件。"""
def _atomic_write(path: Path, content: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise

def _unquote(v: str) -> str:
    if len(v) >= 2 and v[0] == v[-1] == '"':
        try:
            return json.loads(v)
        except ValueError:
            return v[1:-1]
    if len(v) >= 2 and v[0] == v[-1] == "'":
        return v[1:-1].replace("''", "'")
    return v


def parse_skill_md(text: str) -> tuple[dict[str, str], str]:
    """解析内部标准格式的 SKILL.md（简易 frontmatter，不是完整 YAML）。

    支持：单行值、双/单引号值、缩进续行、块标量（> 或 |，按空格折叠）。BOM 会被忽略。
    外部来源的 SKILL.md 请走 SkillImporter（用真正的 YAML 解析）。
    """
    text = text.lstrip("\ufeff")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SkillInvalid("SKILL.md 缺少 frontmatter（应以 --- 开头）")
    front: dict[str, str] = {}
    key: str | None = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            body = "\n".join(lines[i + 1:]).strip()
            return {k: _unquote(v.strip()) for k, v in front.items()}, body
        if line[:1] in (" ", "\t") and key:
            front[key] += " " + line.strip()
        elif ":" in line:
            k, _, v = line.partition(":")
            key = k.strip()
            v = v.strip()
            front[key] = "" if _BLOCK_SCALAR_RE.fullmatch(v) else v
    raise SkillInvalid("SKILL.md 的 frontmatter 未闭合")

"""输出规范化的 SKILL.md。值用 JSON 字符串写出（同时是合法 YAML），避免冒号、引号破坏结构。"""
def render_skill_md(name: str, description: str, instructions: str) -> str:
    n = json.dumps(" ".join(name.split()), ensure_ascii=False)
    d = json.dumps(" ".join(description.split()), ensure_ascii=False)
    return f"---\nname: {n}\ndescription: {d}\n---\n\n{instructions.strip()}\n"


# --------------------------------------------------------------------------- #
# 第 1 层：加载与注册
# --------------------------------------------------------------------------- #
class FileSkillStore:
    """文件系统存储：一个根目录 = 一个 skill 库。"""
    def __init__(self, root: Path | str, *, source: Literal["builtin"] | None = None, read_only: bool = False):
        self.root = Path(root).resolve()
        self.fixed_source = source      # 内置库强制 "builtin"；团队库从 meta.json 读
        self.read_only = read_only

    # -- 路径 ---------------------------------------------------------------
    def _dir(self, skill_id: str) -> Path:
        check_skill_id(skill_id)
        d = (self.root / skill_id).resolve()
        if not d.is_relative_to(self.root):  # 纵深防御，正则已经挡住了 ..
            raise SkillInvalid(f"非法 skill_id: {skill_id!r}")
        return d

    @staticmethod
    def _list_resources(d: Path) -> tuple[str, ...]:
        out = []
        for p in sorted(d.rglob("*")):
            rel = p.relative_to(d)
            if not p.is_file() or any(part.startswith(".") for part in rel.parts):
                continue
            if p.parent == d and p.name in _RESERVED_FILES:
                continue
            out.append(rel.as_posix())
        return tuple(out)

    """skill内置 加载、注册逻辑 """

    # -- 读 读取完整 SKILL.md 指引；此处不过滤 enabled/validation，过滤发生在 Registry.summaries()。 -------------
    def load(self, skill_id: str) -> SkillDetail:
        d = self._dir(skill_id)
        md = d / "SKILL.md"
        if not md.is_file():
            raise SkillNotFound(skill_id)
        try:
            front, body = parse_skill_md(md.read_text(encoding="utf-8"))
            meta_file = d / "meta.json"
            # 缺 meta.json 时按"最不信任"的默认值处理：未启用、待校验
            meta: dict[str, Any] = json.loads(meta_file.read_text(encoding="utf-8")) if meta_file.is_file() else {}
            builtin = self.fixed_source == "builtin"
            return SkillDetail(
                skill_id=skill_id,
                name=front.get("name", ""),
                description=front.get("description", ""),
                instructions=body,
                resources=self._list_resources(d),
                version=str(meta.get("version", "0")),
                updated_at=meta.get("updated_at") or datetime.fromtimestamp(md.stat().st_mtime, tz=timezone.utc),
                allowed_tools=frozenset(meta.get("allowed_tools", [])),
                enabled=bool(meta.get("enabled", False)),
                validation_status=meta.get("validation_status", "pending"),
                source="builtin" if builtin else meta.get("source", "created"),
                requested_tools=frozenset(meta.get("requested_tools", [])),
                package_meta=dict(meta.get("package_meta", {})),
            )
        except (OSError, ValueError) as e:  # JSONDecodeError / pydantic.ValidationError 都是 ValueError
            raise SkillInvalid(f"{skill_id}: {e}") from e


    def load_all(self) -> tuple[list[SkillDetail], dict[str, str]]:
        """返回 (成功加载的 skill, {skill_id: 错误原因})。一个坏 skill 不影响其他。"""
        found: list[SkillDetail] = []
        errors: dict[str, str] = {}
        if not self.root.is_dir():
            return found, errors
        dirs = sorted(p.parent for p in self.root.rglob("SKILL.md"))
        skill_dirs = set(dirs)
        for d in dirs:
            rel = d.relative_to(self.root)
            if any(part.startswith(".") for part in rel.parts):
                continue  # 安装过程中的暂存/备份目录
            if any(parent in skill_dirs for parent in d.parents):
                continue  # 嵌在另一个 skill 包里的 SKILL.md 视为资源
            sid = rel.as_posix()
            try:
                found.append(self.load(sid))
            except SkillError as e:
                errors[sid] = str(e)
        return found, errors


    def resolve_resource(self, skill_id: str, rel_path: str) -> Path:
        """把资源相对路径解析为真实路径；防路径穿越、防读保留文件。"""
        d = self._dir(skill_id)
        p = (d / rel_path).resolve()  # resolve 会跟随符号链接，下面的检查能挡住逃逸
        if not p.is_relative_to(d) or not p.is_file():
            raise SkillNotFound(f"{skill_id}:{rel_path}")
        if p.parent == d and p.name in _RESERVED_FILES:
            raise SkillNotFound(f"{skill_id}:{rel_path}")
        return p

    # -- 写 -----------------------------------------------------------------
    @staticmethod
    def _write_manifest(d:Path,detail:SkillDetail) -> None:
        meta = {
            "version": detail.version,
            "updated_at": detail.updated_at.isoformat(),
            "allowed_tools": sorted(detail.allowed_tools),
            "enabled": detail.enabled,
            "validation_status": detail.validation_status,
            "source": detail.source,
            "requested_tools": sorted(detail.requested_tools),
            "package_meta": detail.package_meta,
        }
        _atomic_write(d/"SKILL.md",render_skill_md(detail.name,detail.description,detail.instructions))
        _atomic_write(d/"meta.json", json.dumps(meta, ensure_ascii=False, indent=2))


    """原地更新 SKILL.md 和 meta.json，不动已有资源文件。"""
    def save(self, detail: SkillDetail) -> None:
        if self.read_only:
            raise SkillReadOnly(detail.skill_id)
        d = self._dir(detail.skill_id)
        d.mkdir(parents=True, exist_ok=True)
        self._write_manifest(d,detail)

    """安装一个完整的包（SKILL.md + meta.json + 资源）：先写暂存目录，再整体换入，失败可回滚。"""
    def install_package(self, detail: SkillDetail, files: Mapping[str, bytes]) -> None:
        if self.read_only:
            raise SkillReadOnly(detail.skill_id)
        target = self._dir(detail.skill_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(dir=target.parent, prefix=".stg-"))
        backup: Path | None = None
        try:
            staging_root = staging.resolve()
            for rel, content in files.items():
                if rel in _RESERVED_FILES:
                    raise SkillInvalid(f"资源不能使用保留文件名: {rel}")
                p = (staging / rel).resolve()
                if not p.is_relative_to(staging_root):
                    raise SkillInvalid(f"非法资源路径: {rel}")
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(content)
            self._write_manifest(staging, detail)
            if target.exists():
                backup = target.parent / f".old-{staging.name}"
                os.replace(target, backup)
            try:
                os.replace(staging, target)
            except BaseException:
                if backup is not None:
                    os.replace(backup, target)  # 换入失败，恢复旧版本
                    backup = None
                raise
        finally:
            shutil.rmtree(staging, ignore_errors=True)
            if backup is not None:
                shutil.rmtree(backup, ignore_errors=True)

    # 用于页面删除
    def delete(self,skill_id:str) -> None:
        if self.read_only:
            raise SkillReadOnly(skill_id)
        d = self._dir(skill_id)
        if not d.is_dir():
            raise SkillNotFound(skill_id)
        shutil.rmtree(d)