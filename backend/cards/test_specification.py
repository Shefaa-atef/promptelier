import json
import sqlite3

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.cards.specification import DesignSpec, RuleSpecificationProvider
from backend.main import create_app
from backend.test_app import wait_run

PROVIDER = RuleSpecificationProvider()
RAMADAN = 'Create a luxurious premium Ramadan card with a midnight-blue background, golden crescent, glowing stars, and sophisticated Islamic geometric ornaments.'
BOTANICAL = 'Create a premium emerald-green royal botanical card with an engraved crown, leaves and vines, silk texture and rim lighting.'


def test_distinct_complete_briefs_and_determinism():
    a = PROVIDER.interpret(RAMADAN)
    b = PROVIDER.interpret(BOTANICAL)
    assert a == PROVIDER.interpret(RAMADAN)
    assert a.specification.tier == b.specification.tier == 'premium'
    assert a.specification.palette.background == '#101D40'
    assert b.specification.palette.background == '#063F32'
    assert a.specification.motifs == ('crescent', 'stars', 'islamic_geometry')
    assert b.specification.motifs == ('leaves', 'vines', 'crown')
    assert a.specification.composition.focal_point == 'crescent'
    assert b.specification.composition.focal_point == 'crown'
    assert b.specification.composition.layout == 'botanical_crest'
    assert b.specification.surface.style == 'engraved'
    assert b.specification.surface.texture == 'silk'
    assert b.specification.surface.lighting == 'rim_light'


def test_color_only_revision_preserves_geometry_and_parent():
    parent = PROVIDER.interpret(RAMADAN).specification
    original_json = parent.model_dump_json()
    result = PROVIDER.interpret('Change only the colors to emerald green and silver; keep the crescent.', parent)
    assert result.specification.palette.background == '#063F32'
    assert result.specification.palette.ornament == '#AAB8CE'
    assert result.applied_fields and all(p.startswith('palette.') for p in result.applied_fields)
    before, after = parent.model_dump(), result.specification.model_dump()
    before.pop('palette'); after.pop('palette')
    assert before == after
    assert parent.model_dump_json() == original_json


def test_revision_chain_removal_and_density():
    parent = PROVIDER.interpret(RAMADAN).specification
    revised = PROVIDER.interpret('Remove stars and make the ornament sparse', parent).specification
    assert 'stars' not in revised.motifs
    assert revised.composition.density == 'sparse'
    final = PROVIDER.interpret('Change the background to red', revised).specification
    assert final.palette.background == '#531829'
    assert final.motifs == revised.motifs and final.composition == revised.composition
    assert final.seed == parent.seed


@pytest.mark.parametrize('prompt', ['Make the previous card blue instead of green', 'Change from green to blue', 'Replace green with blue'])
def test_replacement_ignores_old_color(prompt):
    parent = PROVIDER.interpret(BOTANICAL).specification
    assert PROVIDER.interpret(prompt,parent).specification.palette.background == '#142F65'


def test_focal_instruction_is_scoped_and_arabic_keywords_work():
    botanical = PROVIDER.interpret(BOTANICAL).specification
    assert PROVIDER.interpret('Add leaves', botanical).specification.composition.focal_point == 'crown'
    assert PROVIDER.interpret('Use central leaves', botanical).specification.composition.focal_point == 'leaves'
    arabic = PROVIDER.interpret('بطاقة رمضان فاخر أزرق ذهبي هلال نجوم').specification
    assert arabic.theme == 'ramadan' and arabic.tier == 'premium'
    assert arabic.composition.focal_point == 'crescent'


def test_new_brief_does_not_inherit_selected_parent(tmp_path):
    with TestClient(create_app(tmp_path/'fresh.db',tmp_path/'outputs')) as client:
        parent = client.post('/api/runs',json={'prompt':RAMADAN}).json()
        fresh = client.post('/api/runs',json={'prompt':BOTANICAL,'parent_id':parent['id']}).json()
        parent=wait_run(client,parent)
        fresh=wait_run(client,fresh)
        assert fresh['route']['intent'] == 'card'
        assert fresh['design']['specification']['theme'] == 'royal_botanical'
        assert fresh['design']['specification']['composition']['focal_point'] == 'crown'


def test_explicit_controls_and_hex_roles():
    spec = PROVIDER.interpret('A normal card, background #123456, ornament #ABCDEF, highlight #FFEEDD, linear gradient, rotational symmetry, dense engraved details, matte, no texture, flat lighting').specification
    assert spec.tier == 'normal'
    assert spec.palette.background == '#123456' and spec.palette.ornament == '#ABCDEF'
    assert spec.palette.highlight == '#FFEEDD' and spec.palette.gradient == 'linear'
    assert spec.composition.symmetry == 'rotational' and spec.composition.density == 'dense'
    assert spec.surface.metallic == 'none' and spec.surface.texture == 'none'
    assert spec.surface.lighting == 'flat'


def test_unknown_revision_is_unchanged_and_disclosed():
    parent = PROVIDER.interpret(RAMADAN).specification
    result = PROVIDER.interpret('Make it look like an underwater cathedral',parent)
    assert result.specification == parent and result.applied_fields == ()
    assert any('No supported' in warning for warning in result.warnings)


def test_empty_and_invalid_contracts_rejected():
    with pytest.raises(ValueError): PROVIDER.interpret('   ')
    data = PROVIDER.interpret(RAMADAN).specification.model_dump()
    data['palette']['background'] = 'not-a-color'
    with pytest.raises(ValidationError): DesignSpec.model_validate(data)


def test_focal_contract_and_explicit_hex_precedence():
    result = PROVIDER.interpret('A gold card with ornament color #ABCDEF and highlight color #123456')
    assert result.specification.palette.ornament == '#ABCDEF'
    assert result.specification.palette.highlight == '#123456'
    data = result.specification.model_dump()
    data['motifs'] = ['stars']
    with pytest.raises(ValidationError): DesignSpec.model_validate(data)
    data = PROVIDER.interpret(RAMADAN).specification.model_dump()
    data['surface']['decorative_layers'] = 99
    with pytest.raises(ValidationError): DesignSpec.model_validate(data)


def test_specification_api_persists_and_supports_legacy(tmp_path):
    database = tmp_path/'specs.db'
    with TestClient(create_app(database,tmp_path/'outputs')) as client:
        a = client.post('/api/runs',json={'prompt':RAMADAN}).json()
        a=wait_run(client,a)
        assert a['status'] == 'completed' and 'cards.zip' in a['outputs']
        b = client.post('/api/runs',json={'prompt':'Change only the colors to emerald green','parent_id':a['id']}).json()
        b=wait_run(client,b)
        assert b['parent_id'] == a['id']
        assert b['design']['specification']['seed'] == a['design']['specification']['seed']
        assert all(f.startswith('palette.') for f in b['design']['applied_fields'])
        assert client.get(f"/api/runs/{a['id']}").json() == a
        assert client.get(f"/api/runs/{b['id']}/download").json()['design'] == b['design']
        video = client.post('/api/runs',json={'prompt':'Create a video advertisement'}).json()
        video=wait_run(client,video)
        assert video['design'] is None and video['status'] == 'completed'
    with TestClient(create_app(database,tmp_path/'outputs')) as client:
        assert client.get(f"/api/runs/{b['id']}").json() == b
        legacy = {**a, 'id':'legacy', 'status':'not_implemented'}
        legacy.pop('design')
        with sqlite3.connect(database) as db:
            db.execute('INSERT INTO runs VALUES (?,?)', ('legacy',json.dumps(legacy)))
        assert client.get('/api/runs/legacy').json()['design'] is None
        result = client.post('/api/runs',json={'prompt':'Make it blue','parent_id':'legacy'}).json()
        assert result['status'] == 'needs_clarification' and result['design'] is None
        assert len(client.get('/api/runs').json()) == 5
