from auto_blog.topic_ideas import parse_ideas_list


def test_parse_ideas_list_from_numbered_text() -> None:
    raw = "1. 첫 번째 아이디어: 설명\n2. 두 번째 아이디어: 설명"
    assert parse_ideas_list(raw) == [
        "첫 번째 아이디어: 설명",
        "두 번째 아이디어: 설명",
    ]
