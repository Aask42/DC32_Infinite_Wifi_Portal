def hsv_to_rgb(h, s, v):
    if s == 0.0:
        return (v, v, v)
    i = int(h * 6.0)  # Assume int() truncates!
    f = (h * 6.0) - i
    p, q, t = int(255 * (v * (1.0 - s))), int(255 * (v * (1.0 - s * f))), int(255 * (v * (1.0 - s * (1.0 - f))))
    v = int(255 * v)
    i %= 6
    if i == 0: return (v, t, p)
    if i == 1: return (q, v, p)
    if i == 2: return (p, v, t)
    if i == 3: return (p, q, v)
    if i == 4: return (t, p, v)
    if i == 5: return (v, p, q)
