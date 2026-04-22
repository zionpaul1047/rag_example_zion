from pathlib import Path
from app.services.parsers.parser_factory import get_parser
from app.utils.text_cleaner import clean_text


def load_documents(data_dir: str) -> list[dict]:
    base_path = Path(data_dir)

    if not base_path.exists():
        raise FileNotFoundError(f"문서 폴더를 찾을 수 없습니다: {data_dir}")

    documents = []

    for file_path in sorted(base_path.iterdir()):
        if not file_path.is_file():
            continue

        try:
            parser = get_parser(file_path)
            document = parser.parse(file_path)

            raw_content = document.get("content", "")
            cleaned_content = clean_text(raw_content)

            if cleaned_content.strip():
                document["content"] = cleaned_content
                documents.append(document)

        except ValueError as e:
            print(f"[건너뜀] {e}")
        except Exception as e:
            print(f"[오류] 파일 처리 실패: {file_path.name} / {e}")

    return documents