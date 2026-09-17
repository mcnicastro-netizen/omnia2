"""Private listing publisher card + contact channel helpers."""
from apps.immocloud.public_portal import _public_publisher, _digits_phone


def test_digits_phone():
    assert _digits_phone("+39 333-111-2222") == "+393331112222"
    assert _digits_phone(None) == ""


def test_publisher_agency():
    pub = _public_publisher(
        is_private=False,
        contact_public=None,
        owner_email=None,
        agency={"display_name": "Casa Roma", "email": "a@ex.com", "phone": "06"},
    )
    assert pub["kind"] == "agency"
    assert pub["accepts_messages"] is True
    assert pub["channels"]["email"] == "a@ex.com"


def test_publisher_private_opt_in_channels():
    pub = _public_publisher(
        is_private=True,
        contact_public={
            "display_name": "Marco",
            "show_email": False,
            "show_phone": True,
            "show_whatsapp": True,
            "phone": "+393331112222",
            "whatsapp": "3331112222",
        },
        owner_email="seller@example.com",
        agency=None,
    )
    assert pub["kind"] == "private"
    assert pub["display_name"] == "Marco"
    assert pub["channels"]["email"] is None  # not shown publicly
    assert pub["channels"]["phone"] == "+393331112222"
    assert pub["channels"]["whatsapp"] == "3331112222"
    assert pub["accepts_messages"] is True  # form still notifies account email


def test_publisher_private_show_email():
    pub = _public_publisher(
        is_private=True,
        contact_public={"show_email": True, "show_phone": False, "show_whatsapp": False},
        owner_email="seller@example.com",
        agency=None,
    )
    assert pub["channels"]["email"] == "seller@example.com"


def test_publisher_private_unreachable_without_email():
    pub = _public_publisher(
        is_private=True,
        contact_public={"show_email": True},
        owner_email=None,
        agency=None,
    )
    assert pub["accepts_messages"] is False
    assert pub["channels"]["email"] is None
