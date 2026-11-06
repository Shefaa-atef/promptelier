"""A deterministic art-direction compiler, not a general language model.

The renderer consumes DesignSpec, never the original free-form prompt. Revisions
start from a validated parent's data and are revalidated after patching.
"""
import hashlib
import re
import unicodedata
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

HexColor = str
Motif = Literal['crescent', 'stars', 'islamic_geometry', 'leaves', 'vines', 'crown', 'rosette']


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class Palette(Contract):
    background: HexColor = Field(default='#101D40', pattern=r'^#[0-9A-Fa-f]{6}$')
    secondary: HexColor = Field(default='#243C69', pattern=r'^#[0-9A-Fa-f]{6}$')
    ornament: HexColor = Field(default='#D8AF58', pattern=r'^#[0-9A-Fa-f]{6}$')
    highlight: HexColor = Field(default='#FFF0BE', pattern=r'^#[0-9A-Fa-f]{6}$')
    gradient: Literal['radial', 'linear', 'none'] = 'radial'


class Composition(Contract):
    layout: Literal['central_medallion', 'botanical_crest', 'ornamental_panel'] = 'central_medallion'
    focal_point: Literal['crescent', 'crown', 'rosette', 'leaves'] = 'rosette'
    symmetry: Literal['bilateral', 'rotational', 'none'] = 'bilateral'
    density: Literal['sparse', 'balanced', 'dense'] = 'balanced'
    # Normalized fractions of the artwork's eventual inner safe area.
    focal_scale: float = Field(default=0.42, ge=0.2, le=0.65)
    negative_space: float = Field(default=0.3, ge=0.1, le=0.6)


class Surface(Contract):
    style: Literal['engraved', 'filigree', 'minimal'] = 'filigree'
    metallic: Literal['gold', 'silver', 'none'] = 'gold'
    texture: Literal['fine_grain', 'silk', 'none'] = 'fine_grain'
    lighting: Literal['soft_glow', 'rim_light', 'flat'] = 'soft_glow'
    decorative_layers: int = Field(default=3, ge=1, le=5)


class DesignSpec(Contract):
    schema_version: Literal['1.0'] = '1.0'
    tier: Literal['normal', 'premium'] = 'normal'
    theme: Literal['ramadan', 'royal_botanical', 'ornamental'] = 'ornamental'
    palette: Palette = Field(default_factory=Palette)
    motifs: tuple[Motif, ...] = Field(default=('rosette',), min_length=1, max_length=7)
    composition: Composition = Field(default_factory=Composition)
    surface: Surface = Field(default_factory=Surface)
    seed: int = Field(ge=0, le=2**32 - 1)

    @model_validator(mode='after')
    def validate_motif_hierarchy(self):
        if len(set(self.motifs)) != len(self.motifs):
            raise ValueError('Motifs must be unique.')
        if self.composition.focal_point not in self.motifs:
            raise ValueError('The focal point must be included in the motif vocabulary.')
        return self


class Interpretation(Contract):
    specification: DesignSpec
    provider: Literal['deterministic-rules-v1', 'local-llm-v1'] = 'deterministic-rules-v1'
    applied_fields: tuple[str, ...]
    warnings: tuple[str, ...]


class SpecificationProvider(Protocol):
    """An optional local LLM must return this same validated result contract."""
    def interpret(self, prompt: str, parent: DesignSpec | None = None) -> Interpretation: ...


COLORS = {
    'midnight blue': ('#101D40', '#243C69'), 'navy': ('#101D40', '#243C69'),
    'blue': ('#142F65', '#38629B'), 'emerald green': ('#063F32', '#16654C'),
    'emerald': ('#063F32', '#16654C'), 'green': ('#124B37', '#327452'),
    'red': ('#531829', '#8A3042'), 'burgundy': ('#3F1026', '#712B47'),
    'purple': ('#2D194C', '#593C80'), 'black': ('#101219', '#292E38'),
    'white': ('#F1ECE0', '#D8CFBD'),
    'أزرق': ('#142F65', '#38629B'), 'اخضر': ('#124B37', '#327452'),
    'أخضر': ('#124B37', '#327452'),
}
ACCENTS = {'gold': ('#D8AF58', '#FFF0BE'), 'golden': ('#D8AF58', '#FFF0BE'),
           'silver': ('#AAB8CE', '#F0F5FF'), 'ذهبي': ('#D8AF58', '#FFF0BE')}
MOTIFS = {
    'crescent': r'crescent|هلال', 'stars': r'stars?|نجوم',
    'islamic_geometry': r'islamic|geometric|geometry|اسلامي|إسلامي|هندسي',
    'leaves': r'leaves|leaf|botanical|foliage|نباتي|أوراق',
    'vines': r'vines?|tendrils?', 'crown': r'crown|تاج', 'rosette': r'rosette|وردة',
}


def normalize(prompt: str) -> str:
    return unicodedata.normalize('NFKC', prompt).casefold().replace('-', ' ')


def contains(text: str, expression: str) -> bool:
    return re.search(r'(?<!\w)(?:' + expression + r')(?!\w)', text) is not None


class RuleSpecificationProvider:
    def interpret(self, prompt: str, parent: DesignSpec | None = None) -> Interpretation:
        if not prompt.strip():
            raise ValueError('A non-empty creative brief is required.')
        text = normalize(prompt)
        # Ignore the old value in "blue instead of green" and "green to blue".
        requested = re.split(r'\binstead of\b', text)[0]
        requested = re.sub(r'\bfrom\s+.+?\s+to\s+', '', requested)
        requested = re.sub(r'\breplace\s+.+?\s+with\s+', '', requested)
        color_only = bool(re.search(r'\b(?:only (?:the )?colou?rs?|colou?rs? only)\b', text))
        seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:4], 'big')
        data = parent.model_dump(mode='json') if parent else DesignSpec(seed=seed).model_dump(mode='json')
        before = parent.model_dump(mode='json') if parent else None
        warnings = []
        touched = set()

        def assign(path, value):
            obj = data
            keys = path.split('.')
            for key in keys[:-1]:
                obj = obj[key]
            obj[keys[-1]] = value
            touched.add(path)

        if not color_only:
            if contains(text, r'normal|standard|عادي'):
                assign('tier', 'normal')
            elif contains(text, r'premium|luxurious|luxury|فاخر'):
                assign('tier', 'premium')
            theme = ('ramadan' if contains(text, r'ramadan|رمضان|رمضاني|رمضانية') else
                     'royal_botanical' if contains(text, r'botanical|foliage|نباتي') else None)
            # Theme presets provide intentional art direction for new briefs only.
            # Revisions never reset existing composition as an accidental side effect.
            if theme:
                assign('theme', theme)
                if not parent:
                    if theme == 'ramadan':
                        assign('motifs', ['crescent', 'stars', 'islamic_geometry'])
                        assign('composition.focal_point', 'crescent')
                    else:
                        assign('motifs', ['leaves', 'vines', 'crown'])
                        assign('composition.layout', 'botanical_crest')
                        assign('composition.focal_point', 'crown')
                        assign('palette.background', '#063F32')
                        assign('palette.secondary', '#16654C')
            motifs = list(data['motifs'])
            for name, pattern in MOTIFS.items():
                if contains(text, pattern):
                    # Limited negation is intentional and documented.
                    removed = re.search(r'\b(?:no|without|remove)\s+(?:the\s+)?(?:glowing\s+)?(?:' + pattern + r')(?!\w)', text)
                    if removed:
                        motifs = [m for m in motifs if m != name]
                    elif name not in motifs:
                        motifs.append(name)
                    touched.add('motifs')
            if motifs != data['motifs']:
                assign('motifs', motifs)
            if data['composition']['focal_point'] not in motifs:
                assign('composition.focal_point', next((m for m in motifs if m in ('crescent','crown','leaves','rosette')), 'rosette'))
                if data['composition']['focal_point'] not in motifs:
                    assign('motifs', motifs + ['rosette'])
                    warnings.append('No supported focal motif remains; a neutral rosette is the fallback focal point.')
            # Explicit focal requests override automatic theme direction.
            for focal in ('crescent', 'crown', 'leaves', 'rosette'):
                if contains(text, r'(?:central|focal)\s+(?:' + MOTIFS[focal] + ')'):
                    assign('composition.focal_point', focal)
            for field, choices in {
                'composition.symmetry': {'bilateral':r'bilateral|mirror|mirrored', 'rotational':r'rotational|radial symmetry', 'none':r'asymmetric|asymmetrical'},
                'composition.density': {'sparse':r'sparse|restrained|minimal', 'balanced':r'balanced', 'dense':r'dense|intricate|richly ornamented'},
                'surface.style': {'engraved':r'engraved|engraving', 'filigree':r'filigree', 'minimal':r'minimal|minimalist'},
                'surface.texture': {'silk':r'silk|silky', 'none':r'no texture|without texture', 'fine_grain':r'fine grain|grain'},
                'surface.lighting': {'soft_glow':r'glow|glowing', 'rim_light':r'rim light|rim lighting', 'flat':r'flat lighting|no glow'},
                'palette.gradient': {'radial':r'radial gradient', 'linear':r'linear gradient', 'none':r'no gradient|solid background'},
            }.items():
                for value, pattern in choices.items():
                    if contains(text, pattern):
                        assign(field, value)
            if contains(text, r'no metallic|non metallic|matte'):
                assign('surface.metallic', 'none')
            if contains(text, r'layered|layered details'):
                assign('surface.decorative_layers', 4)

        # Longest matching color phrase wins, preventing "blue" from erasing midnight-blue.
        matches = [(name, values) for name, values in COLORS.items() if contains(requested, re.escape(name))]
        if matches:
            name, (background, secondary) = max(matches, key=lambda x: len(x[0]))
            assign('palette.background', background)
            assign('palette.secondary', secondary)
            if len([n for n,_ in matches if n not in name]) > 0:
                warnings.append('Multiple background colors recognized; longest matching color phrase selected. Use explicit hex roles for precision.')
        # Explicit role colors take precedence over named palettes.
        explicit_roles = set()
        for role in ('background', 'secondary', 'ornament', 'highlight'):
            match = re.search(r'\b' + role + r'\s*(?:colou?r\s*)?(?:[:=]|to|is)?\s*(#[0-9a-f]{6})\b', requested)
            if match:
                assign('palette.' + role, match[1].upper())
                explicit_roles.add(role)
        for name, (ornament, highlight) in ACCENTS.items():
            if contains(requested, name):
                if 'ornament' not in explicit_roles:
                    assign('palette.ornament', ornament)
                if 'highlight' not in explicit_roles:
                    assign('palette.highlight', highlight)
                if not color_only and not contains(text, r'no metallic|non metallic|matte'):
                    assign('surface.metallic', 'silver' if name == 'silver' else 'gold')
        if not parent:
            warnings.append('Design settings use rule-based interpretation and studio defaults. The separate artwork renderer records whether it uses local AI or the procedural fallback.')
        if not touched:
            warnings.append('No supported design changes recognized. Try a palette, motif, density, or surface instruction.')
        warnings.append('The procedural fallback has a limited motif vocabulary. The AI renderer also receives the original brief, subject to its text-model length limit.')
        spec = DesignSpec.model_validate(data)
        changed = []
        def diff(a, b, prefix=''):
            for key, value in b.items():
                path = prefix + key
                if isinstance(value, dict):
                    diff(a.get(key, {}) if a else {}, value, path + '.')
                elif not a or a.get(key) != value:
                    changed.append(path)
        diff(before, spec.model_dump(mode='json'))
        return Interpretation(specification=spec, applied_fields=tuple(changed), warnings=tuple(warnings))
