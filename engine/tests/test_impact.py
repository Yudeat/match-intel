from app.impact import XT_GRID, impact_score, lines_broken, xt_at


def test_saka_example():
    # ΔxT 0.18, pressure 0.842, 3 lines broken -> about 0.28
    assert abs(impact_score(0.18, 0.842, 3) - 0.28) < 0.01


def test_threat_rises_toward_goal():
    assert xt_at(95, 34) > xt_at(50, 34) > xt_at(10, 34)


def test_grid_shape():
    assert XT_GRID.shape == (12, 16)


def test_lines_broken():
    opps = [(70, 10), (70, 25), (70, 40), (70, 55),
            (55, 10), (55, 25), (55, 40), (55, 55),
            (40, 20), (40, 50)]
    assert lines_broken((30, 34), (80, 34), opps) == 3
    assert lines_broken((60, 34), (80, 34), opps) == 1