from datetime import datetime,timezone
import pytest
from scripts.phase6h_b_resume300 import boundaries

def test_exact_authorized_remaining_boundaries():
    first,n=boundaries(datetime(2024,12,11,19,45,tzinfo=timezone.utc),datetime(2025,1,1,tzinfo=timezone.utc))
    assert first.isoformat()=='2024-12-11T20:00:00+00:00' and n==1937

def test_january_restart_and_other_checkpoint_forbidden():
    for last in (datetime(2024,1,8,tzinfo=timezone.utc),datetime(2024,12,11,20,tzinfo=timezone.utc)):
        with pytest.raises(ValueError):boundaries(last,datetime(2025,1,1,tzinfo=timezone.utc))
