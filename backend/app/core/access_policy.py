"""
Merkezi erişim politikası.

Her API ucunun kimlere açık olduğu bu tabloda tanımlanır ve `enforce_access_policy`
tüm /api/v1 isteklerinde çalışır. Tabloda olmayan bir uç varsayılan olarak yalnızca
süper admine açıktır; test paketi her ucun burada açıkça tanımlandığını doğrular.

Kural türleri:
  PUBLIC       Herkese açık (giriş gerekmez)
  AUTH         Giriş yapmış her kullanıcı
  SUPER_ADMIN  Yalnızca RECDx süper adminleri
  SELF         Yalnızca yolda {actor_id} olarak geçen kullanıcının kendisi
  TENANT       Yolda {tenant_id} olan şirketin kullanıcıları (+ izin).
               content=False: yönetim verisi, süper admin de erişebilir.
               content=True : şirket içeriği, süper admin erişemez (KVKK).
  HANDLER      Giriş + izin; şirket kontrolü uç içinde yapılır (şirket gövde/sorgu
               parametresinden veya kaynaktan çözülür).
"""
import uuid
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from fastapi import Depends, Request
from starlette.routing import compile_path

from app.core.security import (
    CurrentUser, ensure_tenant_content, ensure_tenant_management, forbidden,
    get_current_user, get_optional_user,
)


@dataclass(frozen=True)
class Rule:
    kind: str
    permission: Optional[str] = None
    content: bool = False


PUBLIC = Rule("PUBLIC")
AUTH = Rule("AUTH")
SUPER_ADMIN = Rule("SUPER_ADMIN")
SELF = Rule("SELF")


def TENANT(permission: Optional[str] = None, content: bool = False) -> Rule:
    return Rule("TENANT", permission, content)


def HANDLER(permission: Optional[str] = None) -> Rule:
    return Rule("HANDLER", permission)


P = "/api/v1"
C = f"{P}/company/{{tenant_id}}"
AGENT = f"{C}/ai-agents/{{agent_id}}"

POLICY: Dict[Tuple[str, str], Rule] = {
    # --- Genel ---
    ("GET", f"{P}/health"): PUBLIC,
    ("GET", f"{P}/health/"): PUBLIC,
    ("POST", f"{P}/auth/login"): PUBLIC,
    ("GET", f"{P}/auth/me"): AUTH,
    ("GET", f"{P}/auth/telegram"): AUTH,
    # Her yerden onay (ADIM 7.3): belirteçli bağlantı giriş gerektirmez (belirteç tek kullanımlık, süreli, onaylayıcıya özel)
    ("GET", f"{P}/approvals/{{token}}"): PUBLIC,
    ("POST", f"{P}/approvals/{{token}}"): PUBLIC,
    ("GET", f"{P}/me/approvals"): AUTH,
    ("GET", f"{P}/auth/notification-prefs"): AUTH,
    ("PUT", f"{P}/auth/notification-prefs"): AUTH,
    ("POST", f"{P}/auth/telegram/link"): AUTH,
    ("DELETE", f"{P}/auth/telegram/link"): AUTH,
    ("GET", f"{P}/auth/profile/{{actor_id}}"): SELF,
    ("PUT", f"{P}/auth/profile/{{actor_id}}"): SELF,
    ("POST", f"{P}/auth/password-reset/request"): PUBLIC,
    ("POST", f"{P}/auth/password-reset/confirm"): PUBLIC,

    # --- Web sitesi (herkese açık) ---
    ("GET", f"{P}/tenants/plans"): PUBLIC,
    ("GET", f"{P}/tenants/plans/{{plan_id}}"): PUBLIC,
    ("POST", f"{P}/tenants/purchase-request"): PUBLIC,
    ("POST", f"{P}/tenants/purchase-request/send-code"): PUBLIC,
    ("GET", f"{P}/public/stats"): PUBLIC,
    ("GET", f"{P}/sectors/"): PUBLIC,
    ("GET", f"{P}/sectors/{{code}}"): PUBLIC,
    ("GET", f"{P}/professions/"): PUBLIC,
    ("GET", f"{P}/professions/{{code}}"): PUBLIC,

    # --- Süper Admin: katalog ve platform ---
    ("POST", f"{P}/sectors/"): SUPER_ADMIN,
    ("PUT", f"{P}/sectors/{{code}}"): SUPER_ADMIN,
    ("DELETE", f"{P}/sectors/{{code}}"): SUPER_ADMIN,
    ("POST", f"{P}/professions/"): SUPER_ADMIN,
    ("PUT", f"{P}/professions/{{code}}"): SUPER_ADMIN,
    ("DELETE", f"{P}/professions/{{code}}"): SUPER_ADMIN,

    ("GET", f"{P}/models"): AUTH,
    ("GET", f"{P}/models/"): AUTH,
    ("GET", f"{P}/models/{{model_id}}"): AUTH,
    ("POST", f"{P}/models"): SUPER_ADMIN,
    ("POST", f"{P}/models/"): SUPER_ADMIN,
    ("PUT", f"{P}/models/{{model_id}}"): SUPER_ADMIN,
    ("DELETE", f"{P}/models/{{model_id}}"): SUPER_ADMIN,
    ("POST", f"{P}/models/sync-evren"): SUPER_ADMIN,

    # LLM TL fiyat listesi (ADIM 7.5.1)
    ("GET", f"{P}/system/llm-prices"): SUPER_ADMIN,
    ("POST", f"{P}/system/llm-prices"): SUPER_ADMIN,
    ("PUT", f"{P}/system/llm-prices/cr-rate"): SUPER_ADMIN,
    ("GET", f"{P}/system/permissions"): AUTH,
    ("GET", f"{P}/system/permissions/{{perm_id}}"): AUTH,
    ("POST", f"{P}/system/permissions"): SUPER_ADMIN,
    ("PUT", f"{P}/system/permissions/{{perm_id}}"): SUPER_ADMIN,
    ("DELETE", f"{P}/system/permissions/{{perm_id}}"): SUPER_ADMIN,
    ("GET", f"{P}/system/roles"): AUTH,
    ("POST", f"{P}/system/roles"): SUPER_ADMIN,
    ("PUT", f"{P}/system/roles/{{role_id}}"): SUPER_ADMIN,
    ("DELETE", f"{P}/system/roles/{{role_id}}"): SUPER_ADMIN,
    ("GET", f"{P}/system/settings"): AUTH,
    ("GET", f"{P}/system/settings/default-manifesto-model"): AUTH,
    ("POST", f"{P}/system/settings/default-manifesto-model"): SUPER_ADMIN,
    ("GET", f"{P}/system/settings/models"): SUPER_ADMIN,
    ("PUT", f"{P}/system/settings/models"): SUPER_ADMIN,
    ("GET", f"{P}/system/llm/usage"): SUPER_ADMIN,
    ("POST", f"{P}/system/assistant/chat"): SUPER_ADMIN,
    ("GET", f"{P}/system/assistant/history"): SUPER_ADMIN,
    ("GET", f"{P}/system/email-templates"): SUPER_ADMIN,
    ("POST", f"{P}/system/email-templates"): SUPER_ADMIN,
    ("GET", f"{P}/system/email-templates/{{tmpl_id}}"): SUPER_ADMIN,
    ("PUT", f"{P}/system/email-templates/{{tmpl_id}}"): SUPER_ADMIN,
    ("DELETE", f"{P}/system/email-templates/{{tmpl_id}}"): SUPER_ADMIN,
    ("POST", f"{P}/system/email-templates/{{tmpl_id}}/test-send"): SUPER_ADMIN,
    ("GET", f"{P}/system/schedules"): SUPER_ADMIN,
    ("POST", f"{P}/system/schedules"): SUPER_ADMIN,
    ("PUT", f"{P}/system/schedules/{{sched_id}}"): SUPER_ADMIN,
    ("DELETE", f"{P}/system/schedules/{{sched_id}}"): SUPER_ADMIN,
    ("POST", f"{P}/system/schedules/{{sched_id}}/trigger"): SUPER_ADMIN,

    # Platform departman ve unvan kataloğu (Platform Unvan Bilgisi: herkese açık genel bilgi)
    ("GET", f"{P}/catalog/summary"): AUTH,
    ("GET", f"{P}/catalog/departments"): AUTH,
    ("GET", f"{P}/catalog/titles"): AUTH,
    ("GET", f"{P}/catalog/titles/{{title_id}}"): AUTH,
    ("POST", f"{P}/catalog/departments"): SUPER_ADMIN,
    ("PUT", f"{P}/catalog/departments/{{department_id}}"): SUPER_ADMIN,
    ("DELETE", f"{P}/catalog/departments/{{department_id}}"): SUPER_ADMIN,
    ("POST", f"{P}/catalog/titles"): SUPER_ADMIN,
    ("PUT", f"{P}/catalog/titles/{{title_id}}"): SUPER_ADMIN,
    ("DELETE", f"{P}/catalog/titles/{{title_id}}"): SUPER_ADMIN,
    ("GET", f"{P}/catalog/titles/{{title_id}}/documents"): SUPER_ADMIN,
    ("POST", f"{P}/catalog/titles/{{title_id}}/documents"): SUPER_ADMIN,

    ("GET", f"{P}/actors/job-titles"): AUTH,
    ("GET", f"{P}/actors/job-titles/{{title_id}}"): AUTH,
    ("POST", f"{P}/actors/job-titles/admin"): SUPER_ADMIN,
    ("PUT", f"{P}/actors/job-titles/{{title_id}}"): SUPER_ADMIN,
    ("DELETE", f"{P}/actors/job-titles/{{title_id}}"): SUPER_ADMIN,
    ("POST", f"{P}/actors/job-titles/{{title_id}}/regenerate-prompt"): SUPER_ADMIN,
    ("GET", f"{P}/actors"): HANDLER(),
    ("GET", f"{P}/actors/"): HANDLER(),
    ("POST", f"{P}/actors/"): SUPER_ADMIN,

    # --- Süper Admin: müşteriler, paketler, başvurular ---
    ("POST", f"{P}/tenants/plans"): SUPER_ADMIN,
    ("GET", f"{P}/tenants/odoo/products"): SUPER_ADMIN,
    ("PUT", f"{P}/tenants/plans/{{plan_id}}"): SUPER_ADMIN,
    ("DELETE", f"{P}/tenants/plans/{{plan_id}}"): SUPER_ADMIN,
    ("GET", f"{P}/tenants"): SUPER_ADMIN,
    ("GET", f"{P}/tenants/"): SUPER_ADMIN,
    ("POST", f"{P}/tenants/"): SUPER_ADMIN,
    ("POST", f"{P}/tenants/admin-create"): SUPER_ADMIN,
    ("POST", f"{P}/tenants/generate-manifesto"): SUPER_ADMIN,
    ("GET", f"{P}/tenants/leads"): SUPER_ADMIN,
    ("POST", f"{P}/tenants/leads/{{lead_id}}/approve"): SUPER_ADMIN,
    ("POST", f"{P}/tenants/leads/{{lead_id}}/reject"): SUPER_ADMIN,
    ("POST", f"{P}/tenants/leads/{{lead_id}}/odoo-sync"): SUPER_ADMIN,
    ("GET", f"{P}/tenants/{{tenant_id}}/details"): TENANT("tenant:view"),
    ("PUT", f"{P}/tenants/{{tenant_id}}"): SUPER_ADMIN,
    ("DELETE", f"{P}/tenants/{{tenant_id}}"): SUPER_ADMIN,
    ("POST", f"{P}/tenants/{{tenant_id}}/toggle-status"): SUPER_ADMIN,
    ("PUT", f"{P}/tenants/{{tenant_id}}/admin-user"): SUPER_ADMIN,
    ("POST", f"{P}/tenants/{{tenant_id}}/generate-password"): SUPER_ADMIN,
    ("POST", f"{P}/tenants/{{tenant_id}}/approve"): SUPER_ADMIN,
    ("POST", f"{P}/tenants/{{tenant_id}}/send-welcome"): SUPER_ADMIN,
    ("POST", f"{P}/tenants/{{tenant_id}}/send-reminder"): SUPER_ADMIN,
    ("POST", f"{P}/tenants/{{tenant_id}}/credits/topup"): SUPER_ADMIN,
    ("GET", f"{P}/tenants/{{tenant_id}}/roles"): TENANT("tenant:view"),
    ("POST", f"{P}/tenants/{{tenant_id}}/roles"): TENANT("role:create"),

    # --- Müşteri Yönetim Merkezi (yönetim verisi: süper admin de erişebilir) ---
    ("GET", f"{C}/departments"): TENANT("tenant:view"),
    ("GET", f"{C}/catalog/recommended"): TENANT("tenant:view"),
    ("POST", f"{C}/departments/from-catalog"): TENANT("tenant:manage"),
    ("GET", f"{C}/hire/options"): TENANT("agent:hire"),
    ("GET", f"{C}/hire/titles"): TENANT("agent:hire"),
    ("GET", f"{C}/hire/preview"): TENANT("agent:hire"),
    ("POST", f"{C}/departments"): TENANT("tenant:manage"),
    ("PUT", f"{C}/departments/{{department_id}}"): TENANT("tenant:manage"),
    ("DELETE", f"{C}/departments/{{department_id}}"): TENANT("tenant:manage"),
    ("GET", f"{C}/job-titles/system-templates"): TENANT("tenant:view"),
    ("GET", f"{C}/job-titles"): TENANT("tenant:view"),
    ("POST", f"{C}/job-titles"): TENANT("agent:custom_title"),
    ("PUT", f"{C}/job-titles/{{title_id}}"): TENANT("agent:custom_title"),
    ("DELETE", f"{C}/job-titles/{{title_id}}"): TENANT("agent:custom_title"),
    ("GET", f"{C}/llm-models"): TENANT("tenant:view"),
    ("GET", f"{C}/entitlements"): TENANT("tenant:view"),
    ("POST", f"{C}/generate-role-prompt"): TENANT("agent:configure"),
    ("GET", f"{C}/ai-agents"): TENANT("tenant:view"),
    ("POST", f"{C}/ai-agents"): TENANT("agent:hire"),
    ("PUT", f"{AGENT}"): TENANT("agent:configure"),
    ("POST", f"{AGENT}/terminate"): TENANT("agent:hire"),
    ("POST", f"{AGENT}/rehire"): TENANT("agent:hire"),
    ("DELETE", f"{AGENT}"): TENANT("agent:hire"),
    ("GET", f"{C}/agent-quota"): TENANT("tenant:view"),
    ("POST", f"{C}/ai-agents/deep-search-sector-title"): TENANT("agent:hire"),
    ("PUT", f"{C}/manifesto"): TENANT("tenant:manage"),
    ("POST", f"{C}/generate-manifesto"): TENANT("tenant:manage"),
    ("GET", f"{C}/user-quota"): TENANT("tenant:view"),
    ("GET", f"{C}/credits"): TENANT("billing:view"),
    ("GET", f"{C}/brain/settings"): TENANT("tenant:view"),
    ("PUT", f"{C}/brain/settings"): TENANT("tenant:manage"),
    ("GET", f"{C}/users"): TENANT("tenant:view"),
    ("POST", f"{C}/users"): TENANT("user:manage"),
    ("PUT", f"{C}/users/{{user_id}}"): TENANT("user:manage"),
    ("DELETE", f"{C}/users/{{user_id}}"): TENANT("user:manage"),

    # --- AI personel öğrenme kaynakları (şirket içeriği: süper admin erişemez) ---
    ("GET", f"{AGENT}/documents"): TENANT("tenant:view", content=True),
    ("POST", f"{AGENT}/documents"): TENANT("agent:configure", content=True),
    ("DELETE", f"{AGENT}/documents/{{document_id}}"): TENANT("agent:configure", content=True),
    ("GET", f"{AGENT}/documents/{{document_id}}/download"): TENANT("tenant:view", content=True),
    ("POST", f"{AGENT}/web-links"): TENANT("agent:configure", content=True),
    ("POST", f"{AGENT}/video-links"): TENANT("agent:configure", content=True),
    ("POST", f"{AGENT}/deep-search"): TENANT("agent:configure", content=True),
    ("POST", f"{AGENT}/deep-search-sector-title"): TENANT("agent:configure", content=True),
    ("GET", f"{C}/job-titles/{{title_id}}/documents"): TENANT("tenant:view", content=True),
    ("POST", f"{C}/job-titles/{{title_id}}/documents"): TENANT("agent:configure", content=True),

    # --- Öğrenme dokümanı işlemleri (yetki dokümanın katmanından uç içinde çözülür) ---
    ("GET", f"{P}/documents/{{document_id}}"): HANDLER(),
    ("GET", f"{P}/documents/{{document_id}}/download"): HANDLER(),
    ("POST", f"{P}/documents/{{document_id}}/approve"): HANDLER(),
    ("POST", f"{P}/documents/{{document_id}}/reject"): HANDLER(),
    ("POST", f"{P}/documents/{{document_id}}/test"): HANDLER(),
    ("POST", f"{P}/documents/{{document_id}}/reprocess"): HANDLER(),
    ("POST", f"{P}/documents/{{document_id}}/versions"): HANDLER(),
    ("DELETE", f"{P}/documents/{{document_id}}"): HANDLER(),
    ("GET", f"{P}/projects/{{project_id}}/documents"): HANDLER(),
    ("POST", f"{P}/projects/{{project_id}}/documents"): HANDLER(),
    ("POST", f"{P}/projects/{{project_id}}/knowledge/promote"): HANDLER("memory:promote"),
    ("GET", f"{AGENT}/knowledge"): TENANT("tenant:view", content=True),
    ("POST", f"{AGENT}/knowledge/search"): TENANT("tenant:view", content=True),

    # --- Beyin AI (manifesto, hafıza ve sohbet içerir: süper admin erişemez) ---
    ("POST", f"{C}/brain/chat"): TENANT("chat:participate", content=True),
    ("GET", f"{C}/brain/history"): TENANT("chat:participate", content=True),

    # --- Work Space içeriği (şirket kontrolü uç içinde) ---
    ("GET", f"{P}/projects"): HANDLER(),
    ("GET", f"{P}/projects/"): HANDLER(),
    ("POST", f"{P}/projects"): HANDLER("project:create"),
    ("POST", f"{P}/projects/"): HANDLER("project:create"),
    ("GET", f"{P}/projects/{{project_id}}"): HANDLER(),
    ("PUT", f"{P}/projects/{{project_id}}"): HANDLER(),
    ("POST", f"{P}/projects/{{project_id}}/status"): HANDLER(),
    ("POST", f"{P}/projects/{{project_id}}/members"): HANDLER(),
    ("DELETE", f"{P}/projects/{{project_id}}/members/{{actor_id}}"): HANDLER(),
    ("POST", f"{P}/projects/{{project_id}}/plan/suggest"): HANDLER(),
    ("PUT", f"{P}/projects/{{project_id}}/plan"): HANDLER(),
    ("POST", f"{P}/projects/{{project_id}}/plan/approve"): HANDLER(),
    ("GET", f"{P}/projects/{{project_id}}/plan/chat"): HANDLER(),
    ("POST", f"{P}/projects/{{project_id}}/plan/chat"): HANDLER(),
    ("POST", f"{P}/projects/{{project_id}}/simulate"): HANDLER(),
    ("GET", f"{P}/projects/{{project_id}}/tasks"): HANDLER(),
    ("POST", f"{P}/projects/{{project_id}}/tasks"): HANDLER("task:create"),
    # İş akışı (ADIM 7.1): yetki proje üyeliği/onaylayıcılığa göre uç içinde
    ("GET", f"{P}/projects/{{project_id}}/workflow"): HANDLER(),
    ("GET", f"{P}/projects/{{project_id}}/costs"): HANDLER(),
    # Maliyet kalemleri ve bütçe (ADIM 7.5.3): proje yöneticisi
    ("GET", f"{P}/projects/{{project_id}}/cost-items"): HANDLER(),
    ("POST", f"{P}/projects/{{project_id}}/cost-items"): HANDLER(),
    ("PUT", f"{P}/projects/{{project_id}}/cost-items/{{item_id}}"): HANDLER(),
    ("DELETE", f"{P}/projects/{{project_id}}/cost-items/{{item_id}}"): HANDLER(),
    ("POST", f"{P}/projects/{{project_id}}/cost-items/{{item_id}}/attachment"): HANDLER(),
    ("GET", f"{P}/projects/{{project_id}}/cost-items/{{item_id}}/attachment"): HANDLER(),
    ("PUT", f"{P}/projects/{{project_id}}/budget"): HANDLER(),
    ("GET", f"{P}/projects/{{project_id}}/costs/export.xlsx"): HANDLER(),
    ("POST", f"{P}/live/ticket"): HANDLER(),
    ("GET", f"{P}/projects/{{project_id}}/repository"): HANDLER(),
    ("PUT", f"{P}/projects/{{project_id}}/repository"): HANDLER(),
    ("GET", f"{P}/projects/{{project_id}}/repository/file"): HANDLER(),
    ("POST", f"{P}/projects/{{project_id}}/repository/steps/{{task_id}}/merge"): HANDLER(),
    ("POST", f"{P}/tasks/{{task_id}}/submit"): HANDLER(),
    ("POST", f"{P}/tasks/{{task_id}}/decision"): HANDLER(),
    ("POST", f"{P}/tasks/{{task_id}}/release"): HANDLER(),
    ("GET", f"{P}/tasks/{{task_id}}/artifacts/{{artifact_id}}"): HANDLER(),
    ("GET", f"{P}/chat/history/{{task_id}}"): HANDLER(),
    ("GET", f"{P}/chat/project/{{project_id}}"): HANDLER(),
    ("POST", f"{P}/chat/send"): HANDLER("chat:participate"),
    ("POST", f"{P}/chat/learn/{{task_id}}"): HANDLER("chat:participate"),
    ("GET", f"{P}/memory"): HANDLER(),
    ("GET", f"{P}/memory/"): HANDLER(),
    ("POST", f"{P}/memory/add"): HANDLER("memory:promote"),
    ("POST", f"{P}/memory/search"): HANDLER("memory:search"),
    ("POST", f"{P}/memory/promote/{{memory_id}}"): HANDLER("memory:promote"),
    ("POST", f"{P}/memory/{{memory_id}}/reject"): HANDLER("memory:promote"),
    ("POST", f"{P}/memory/{{memory_id}}/revoke"): HANDLER("memory:promote"),
}


# Şablonlar Starlette yol derleyicisiyle eşleştirilir; en özel (en az parametreli) şablon önce denenir.
_COMPILED = sorted(
    ((method, template, compile_path(template)[0], rule) for (method, template), rule in POLICY.items()),
    key=lambda item: item[1].count("{"),
)


def match_rule(method: str, path: str) -> Tuple[Optional[str], Rule]:
    """İstek yoluna karşılık gelen şablonu ve kuralı döner; tanımsızsa süper admin kuralı."""
    for m, template, regex, rule in _COMPILED:
        if m == method and regex.match(path):
            return template, rule
    return None, SUPER_ADMIN


async def enforce_access_policy(request: Request, user: Optional[CurrentUser] = Depends(get_optional_user)) -> None:
    template, rule = match_rule(request.method, request.url.path)
    request.state.route_path = template or request.url.path
    request.state.path_params = dict(request.path_params)

    if rule.kind == "PUBLIC":
        return

    user = await get_current_user(user)

    if rule.kind == "AUTH":
        return
    if rule.kind == "SUPER_ADMIN":
        if not user.is_super_admin:
            raise forbidden("Bu işlem yalnızca RECDx süper yöneticilerine açıktır.")
        return
    if rule.kind == "SELF":
        if str(request.path_params.get("actor_id")) != str(user.actor_id):
            raise forbidden("Yalnızca kendi profilinizi görüntüleyebilir ve düzenleyebilirsiniz.")
        return
    if rule.kind == "TENANT":
        try:
            tenant_id = uuid.UUID(str(request.path_params.get("tenant_id")))
        except ValueError:
            raise forbidden("Geçersiz şirket kimliği.")
        request.state.tenant_id = tenant_id
        if rule.content:
            ensure_tenant_content(user, tenant_id, rule.permission)
        else:
            ensure_tenant_management(user, tenant_id, rule.permission)
        return
    if rule.kind == "HANDLER":
        if rule.permission and not user.has(rule.permission):
            raise forbidden()
        return
    raise forbidden()
