from tesla_monitor import monitor


class FakeNotifier:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)


VEHICLE_MATCH = {
    "VIN": "VIN1",
    "Model": "my",
    "TrimName": "Long Range",
    "Price": 44000,
    "OptionCodeData": [],
}

VEHICLE_NO_MATCH = {
    "VIN": "VIN2",
    "Model": "my",
    "TrimName": "Performance",
    "Price": 60000,
    "OptionCodeData": [],
}

CFG = {
    "tesla": {"model": "my", "market": "PT"},
    "filters": {"price_max": 47000},
}


def test_run_once_notifies_new_match(monkeypatch, tmp_path):
    monkeypatch.setattr(monitor.tesla_api, "fetch_all_inventory", lambda cfg: [VEHICLE_MATCH])
    notifier = FakeNotifier()
    state_path = str(tmp_path / "state.json")

    matches = monitor.run_once(CFG, [notifier], state_path, "https://example.com")

    assert len(matches) == 1
    assert len(notifier.sent) == 1
    assert "Novo Tesla disponível" in notifier.sent[0]


def test_run_once_does_not_renotify_seen_vehicle(monkeypatch, tmp_path):
    monkeypatch.setattr(monitor.tesla_api, "fetch_all_inventory", lambda cfg: [VEHICLE_MATCH])
    notifier = FakeNotifier()
    state_path = str(tmp_path / "state.json")

    monitor.run_once(CFG, [notifier], state_path, "https://example.com")
    notifier.sent.clear()
    matches = monitor.run_once(CFG, [notifier], state_path, "https://example.com")

    assert matches == []
    assert notifier.sent == []


def test_run_once_sends_not_available_message_when_requested(monkeypatch, tmp_path):
    monkeypatch.setattr(monitor.tesla_api, "fetch_all_inventory", lambda cfg: [VEHICLE_NO_MATCH])
    notifier = FakeNotifier()
    state_path = str(tmp_path / "state.json")

    matches = monitor.run_once(
        CFG, [notifier], state_path, "https://example.com", notify_on_empty=True
    )

    assert matches == []
    assert len(notifier.sent) == 1
    assert "Sem unidades disponíveis" in notifier.sent[0]


def test_run_once_stays_silent_on_empty_by_default(monkeypatch, tmp_path):
    monkeypatch.setattr(monitor.tesla_api, "fetch_all_inventory", lambda cfg: [VEHICLE_NO_MATCH])
    notifier = FakeNotifier()
    state_path = str(tmp_path / "state.json")

    matches = monitor.run_once(CFG, [notifier], state_path, "https://example.com")

    assert matches == []
    assert notifier.sent == []
