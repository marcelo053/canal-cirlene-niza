# tests/test_agents/test_produzir_flow.py
import pytest
from unittest.mock import MagicMock, patch
from cirleneniza.crew.produzir_flow import ProduzirFlow, ProductionState


def test_production_state_defaults():
    state = ProductionState(topic="proteína")
    assert state.topic == "proteína"
    assert state.production_id is None
    assert state.research is None
    assert state.script is None


def test_produzir_flow_has_required_phases():
    flow = ProduzirFlow.__new__(ProduzirFlow)
    assert hasattr(flow, "pesquisar")
    assert hasattr(flow, "escrever_roteiro")
    assert hasattr(flow, "revisar")
    assert hasattr(flow, "produzir")


def test_produzir_flow_instantiates_all_agents():
    with patch("cirleneniza.crew.produzir_flow.CalendarioEditorial"), \
         patch("cirleneniza.crew.produzir_flow.RoteiristaCirleneNiza"), \
         patch("cirleneniza.crew.produzir_flow.RevisorEspecialista"), \
         patch("cirleneniza.crew.produzir_flow.Narrador"), \
         patch("cirleneniza.crew.produzir_flow.EditorAudio"), \
         patch("cirleneniza.crew.produzir_flow.GeradorDePrompts"), \
         patch("cirleneniza.crew.produzir_flow.GeradorCenas"), \
         patch("cirleneniza.crew.produzir_flow.DiretorDeArte"), \
         patch("cirleneniza.crew.produzir_flow.EditorVideo"), \
         patch("cirleneniza.crew.produzir_flow.Publicador"), \
         patch("cirleneniza.crew.produzir_flow.get_settings") as mock_cfg, \
         patch("cirleneniza.crew.produzir_flow.MinIOClient"), \
         patch("cirleneniza.crew.produzir_flow.HeyGenClient"), \
         patch("cirleneniza.crew.produzir_flow.BaserowClient"), \
         patch("cirleneniza.crew.produzir_flow.CostTracker"), \
         patch("cirleneniza.crew.produzir_flow.NCAToolkitClient"), \
         patch("cirleneniza.crew.produzir_flow.GeradorSlidesCientificos"):
        mock_cfg.return_value = MagicMock()
        flow = ProduzirFlow()
        assert flow.calendario is not None
        assert flow.roteirista is not None
        assert flow.revisor is not None
