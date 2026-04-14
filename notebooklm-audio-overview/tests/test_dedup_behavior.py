from skills.notebooklm_audio_overview import normalize_request


def test_deduplicates_links_after_normalization() -> None:
    request = normalize_request(
        {
            "links": [
                " https://Example.com/path/#section ",
                "https://example.com/path",
                "https://example.com/path/",
                "https://example.com/path?x=1",
            ],
            "notebook_name": "Research Briefing",
        }
    )

    assert request.links == (
        "https://example.com/path",
        "https://example.com/path?x=1",
    )
