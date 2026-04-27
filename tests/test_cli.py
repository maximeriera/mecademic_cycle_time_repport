from mecademic_cycle_report.cli import build_parser


def test_analyze_parser_accepts_enforce_sim_mode_override() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "analyze",
            "program.mxprog",
            "--config",
            "config.yaml",
            "--enforce-sim-mode",
        ]
    )

    assert args.enforce_sim_mode is True
    assert args.no_enforce_sim_mode is False


def test_analyze_parser_accepts_no_enforce_sim_mode_override() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "analyze",
            "program.mxprog",
            "--config",
            "config.yaml",
            "--no-enforce-sim-mode",
        ]
    )

    assert args.enforce_sim_mode is False
    assert args.no_enforce_sim_mode is True