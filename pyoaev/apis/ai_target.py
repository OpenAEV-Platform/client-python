from pyoaev.base import RESTManager, RESTObject
from pyoaev.mixins import CreateMixin, DeleteMixin, GetMixin, ListMixin, UpdateMixin
from pyoaev.utils import RequiredOptional


class AiTarget(RESTObject):
    _id_attr = "asset_id"


class AiTargetManager(
    GetMixin, ListMixin, CreateMixin, UpdateMixin, DeleteMixin, RESTManager
):
    """Manage AI Target assets (LLM endpoints / AI agents under adversarial test)."""

    _path = "/ai_targets"
    _obj_cls = AiTarget
    _create_attrs = RequiredOptional(
        required=("asset_name", "ai_target_provider"),
        optional=(
            "asset_description",
            "asset_tags",
            "asset_external_reference",
            "ai_target_endpoint",
            "ai_target_model",
            "ai_target_modality",
            "ai_target_system_prompt",
            "ai_target_token",
            "ai_target_configuration",
        ),
    )
