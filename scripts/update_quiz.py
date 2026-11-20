
import json
import pathlib
import urllib.request
import html
import random
import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "news.json"

API_URL = (
    "https://opentdb.com/api.php"
    "?amount=5&type=multiple&encode=default"
)

def get_questions():
    request = urllib.request.Request(
        API_URL,
        headers={"User-Agent": "DailyWidgets/1.0"}
    )

    with urllib.request.urlopen(
        request, timeout=25
    ) as response:
        payload = json.load(response)

    if payload.get("response_code") != 0:
        raise RuntimeError(
            "Trivia API returned no questions"
        )

    questions = []

    for item in payload["results"]:
        correct = html.unescape(
            item["correct_answer"]
        )

        answers = [
            html.unescape(answer)
            for answer in item["incorrect_answers"]
        ]
        answers.append(correct)
        random.shuffle(answers)

        questions.append({
            "question": html.unescape(
                item["question"]
            ),
            "options": answers,
            "answer": correct,
            "category": html.unescape(
                item.get("category", "")
            ),
            "explanation": (
                "Correct answer: " + correct
            )
        })

    return questions

def main():
    data = json.loads(
        DATA_FILE.read_text(encoding="utf-8")
    )

    data["quiz"] = get_questions()
    data["quiz_updated_at"] = (
        datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()
    )

    DATA_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    print("Saved 5 quiz questions")

if __name__ == "__main__":
    main()
