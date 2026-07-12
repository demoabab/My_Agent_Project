from typing import Optional

from chatchat.server.db.models.user_profile_model import UserProfileModel
from chatchat.server.db.session import with_session


@with_session
def get_user_profile(session, user_id: str) -> Optional[dict]:
    profile = session.query(UserProfileModel).filter(UserProfileModel.user_id == user_id).first()
    if not profile:
        return None
    return {
        "user_id": profile.user_id,
        "preferred_model": profile.preferred_model,
        "language": profile.language,
        "response_style": profile.response_style,
        "expertise_domain": profile.expertise_domain,
        "key_facts": profile.key_facts or [],
    }


@with_session
def upsert_user_profile(session, user_id: str, **fields) -> None:
    profile = session.query(UserProfileModel).filter(UserProfileModel.user_id == user_id).first()
    if profile:
        for k, v in fields.items():
            if v is not None and hasattr(profile, k):
                setattr(profile, k, v)
        session.add(profile)
    else:
        valid_fields = {}
        for k, v in fields.items():
            if v is not None and hasattr(UserProfileModel, k):
                valid_fields[k] = v
        valid_fields["user_id"] = user_id
        session.add(UserProfileModel(**valid_fields))


@with_session
def append_key_facts(session, user_id: str, facts: list) -> None:
    profile = session.query(UserProfileModel).filter(UserProfileModel.user_id == user_id).first()
    if profile:
        existing = set(profile.key_facts or [])
        existing.update(facts)
        profile.key_facts = list(existing)
        session.add(profile)
    else:
        session.add(UserProfileModel(user_id=user_id, key_facts=list(facts)))
