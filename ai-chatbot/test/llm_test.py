import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

def main():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("API 키가 없습니다.")
        return

    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0
    )

    result = llm.invoke("안녕하세요. 한 줄로 자기소개 해주세요.")
    print(result.content)

if __name__ == "__main__":
    main()