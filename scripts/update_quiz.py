
import json
import pathlib
import urllib.request
import urllib.error
import html
import random
import datetime
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "news.json"

API_URL = (
    "https://opentdb.com/api.php"
    "?amount=5&type=multiple"
)


def get_questions():
    request = urllib.request.Request(
        API_URL,
        headers={
            "User-Agent": "DailyWidgets/1.0",
            "Accept": "application/json"
        }
    )

    with urllib.request.urlopen(
        request, timeout=25
    ) as response:
        payload = json.load(response)

    code = payload.get("response_code")

    if code != 0:
        raise RuntimeError(
            f"Trivia API error code: {code}"
        )

    results = payload.get("results", [])

    if len(results) != 5:
        raise RuntimeError(
            f"Expected 5 questions, got {len(results)}"
        )

    questions = []

    for item in results:
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


def get_questions_with_retry():
    for attempt in range(1, 4):
        try:
            print(
                f"Fetching quiz: attempt {attempt}/3"
            )
            return get_questions()

        except Exception as error:
            print(
                f"Attempt {attempt} failed: {error}"
            )

            if attempt == 3:
                raise

            time.sleep(15)


def main():
    data = json.loads(
        DATA_FILE.read_text(encoding="utf-8")
    )

    questions = get_questions_with_retry()

    data["quiz"] = questions

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

    print("Successfully saved 5 quiz questions")


if __name__ == "__main__":
    main()
