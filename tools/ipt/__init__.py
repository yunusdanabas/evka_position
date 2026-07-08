"""tools.ipt — Quick IPT hidden-point measurement for evka_position.

Recovers a target point that cannot be touched directly: the operator holds a pen
TIP fixed on the hidden target and sweeps the handle. The wire attaches to the pen
BODY (offset L from the tip), so every measured Cartesian point lies on a sphere
of radius L centred on the target. Fitting that sphere returns the target.

See the project plan and patent US 9,267,794 B2 (Prodim) for the model.
"""
