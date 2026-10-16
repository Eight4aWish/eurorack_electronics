"""Placement helpers shared by the sheet builders."""

from parts import CAP, FP_C, FP_R, ICS, RES, holes_part

NC = None  # marks a pin as deliberately unconnected


def _fields(p, extra=None):
    f = {}
    if p.get("lcsc"):
        f["LCSC"] = p["lcsc"]
    if p.get("mpn"):
        f["MPN"] = p["mpn"]
    f["JLC"] = p.get("jlc", "")
    if p.get("note"):
        f["Note"] = p["note"]
    f.update(extra or {})
    return f


def part(sh, key, at, rot=0, mirror=None, unit=1, ref=None, value=None, fields=None, p=None, dnp=False, **kw):
    p = p or ICS[key]
    in_bom = p.get("jlc") not in ("bare holes", "bare pad")
    return sh.place(p["lib"], ref=ref, value=value or p["value"], at=at, rot=rot, mirror=mirror, unit=unit,
                    footprint=p["fp"], datasheet=p.get("ds", ""), fields=_fields(p, fields), in_bom=in_bom,
                    prefix=p.get("prefix", "U"), dnp=dnp, **kw)


def ic(sh, key, at, nets, rot=0, mirror=None, unit=1, ref=None, value=None, stub=2.54, fields=None, p=None, stubs=None,
       hide_value=False, **kw):
    """Place a part and tie every pin (of this unit) to a net with a stub and label / power symbol.
    `nets` maps pin number -> net name, or NC. Pins stacked at one position are tied together.
    Raises if any pin of the unit is left out, so nothing is forgotten."""
    pl = part(sh, key, at, rot, mirror, unit, ref, value, fields, p, hide_value=hide_value, **kw)
    nets = {str(k): v for k, v in nets.items()}
    groups = {}
    for n, pin in pl.pins.items():
        groups.setdefault(pl.p(n), []).append(n)
    for pos, nums in groups.items():
        given = {nets[n] for n in nums if n in nets}
        missing = [n for n in nums if n not in nets]
        if len(given) > 1:
            raise ValueError(f"{pl.ref}: stacked pins {nums} given different nets {given}")
        if not given:
            raise ValueError(f"{pl.ref} ({key}): pins {missing} not assigned")
        net = given.pop()
        vis = [n for n in nums if not pl.pins[n].hidden] or nums
        if net is NC:
            if all(pl.pins[n].etype == "no_connect" for n in nums):
                for n in nums:
                    sh.connections.append((pl.ref, n, None, pos))
            else:
                sh.no_connect(pl, vis[0])
                for n in nums[1:]:
                    sh.connections.append((pl.ref, n, None, pos))
            continue
        sh.connect(pl, vis[0], net, stub=(stubs or {}).get(vis[0], (stubs or {}).get(int(vis[0]) if vis[0].isdigit() else vis[0], stub)),
                   outward=True)
        for n in nums:
            if n != vis[0]:
                sh.connections.append((pl.ref, n, net, pos))
    extra = set(nets) - set(pl.pins)
    if extra:
        raise ValueError(f"{pl.ref}: nets given for pins not on this unit: {sorted(extra)}")
    return pl


def R(sh, value, at, rot=0, size="0402", ref=None, fields=None, dnp=False, text_left=False):
    f = {"LCSC": RES[(value, size)], "JLC": "Basic", "Tolerance": "1%"}
    f.update(fields or {})
    return sh.place("Device:R_Small", ref=ref, value=value, at=at, rot=rot, footprint=FP_R[size],
                    fields=f, prefix="R", dnp=dnp, text_left=text_left)


def C(sh, value, at, rot=0, size="0402", ref=None, decouples=None, fields=None, dnp=False, lcsc=True, text_left=False):
    entry = CAP[(value, size)]
    code, volts, diel = entry[:3]
    jlc = entry[3] if len(entry) > 3 else "Basic"
    f = {"LCSC": code if lcsc else "", "JLC": jlc, "Voltage": volts, "Dielectric": diel}
    if decouples:
        f["Decouples"] = decouples
    f.update(fields or {})
    return sh.place("Device:C_Small", ref=ref, value=f"{value} {volts}", at=at, rot=rot, footprint=FP_C[size],
                    fields=f, prefix="C", dnp=dnp, text_left=text_left)


def decap(sh, at, value, size, rail, decouples, gnd="GND"):
    """Vertical capacitor from rail (top) to ground (bottom), drawn with power symbols."""
    c = C(sh, value, at, size=size, decouples=decouples)
    sh.connect(c, 1, rail, stub=0)
    sh.connect(c, 2, gnd, stub=0)
    return c


def decaps(sh, x, y, rail, specs, decouples, pitch=12.7):
    """A row of decoupling caps left to right. specs: [(value, size), ...]."""
    out = []
    for i, (v, s) in enumerate(specs):
        out.append(decap(sh, (x + i * pitch, y), v, s, rail, decouples))
    return out


def two_pin(sh, pl, net1, net2, stub=2.54):
    sh.connect(pl, 1, net1, stub=stub)
    sh.connect(pl, 2, net2, stub=stub)
    return pl


def holes(sh, at, nets, title, ref=None, rot=0, mirror=None, stubs=None):
    """A row of bare plated holes (the wiring field), one per entry of `nets` (top to bottom)."""
    p = holes_part(nets, tuple(sh.project.ground_nets))
    p = dict(p, value=title)
    return ic(sh, None, at, {i + 1: n for i, n in enumerate(nets)}, rot=rot, mirror=mirror, ref=ref, p=p, stubs=stubs)


def tp(sh, at, net, ref=None, label=None):
    """Test pad. Positive rails: pad below, pin up to the rail symbol. Everything else: pin down."""
    p = dict(ICS["TP"], value=label or net)
    up = net in sh.project.power_nets and net not in sh.project.ground_nets
    t = part(sh, "TP", at, p=p, ref=ref, rot=180 if up else 0, hide_value=True)
    sh.connect(t, 1, net, stub=2.54)
    return t
