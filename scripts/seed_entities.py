from backend.app.core.database import SessionLocal, init_db
from backend.app.services.entity_extraction_service import ExtractedEntity
from backend.app.services.entity_extraction_service import COMPANY_TERMS, TECH_TERMS
from backend.app.services.storage_service import StorageService, seed_sources
from backend.app.utils.text_utils import canonicalize_name


def main() -> None:
    init_db()
    with SessionLocal() as db:
        seed_sources(db)
        storage = StorageService(db)
        for term in TECH_TERMS:
            storage.get_or_create_entity(
                ExtractedEntity(name=term, canonical_name=canonicalize_name(term), entity_type="technology")
            )
        for term in COMPANY_TERMS:
            storage.get_or_create_entity(
                ExtractedEntity(name=term, canonical_name=canonicalize_name(term), entity_type="company")
            )
        db.commit()


if __name__ == "__main__":
    main()
