import math
BRAILLE_BASE = 0x2800
# bit positions for braille (2x4 matrix)
DOTS = [(0,0,1), (0,1,2), (0,2,3), (1,0,4), (1,1,5), (1,2,6), (0,3,7), (1,3,8)]

def braille_from_points(points):
    # points: list of (x,y) where x in {0,1}, y in {0..3}
    acc = 0
    for x,y in points:
        for bx,by,bit in DOTS:
            if x==bx and y==by:
                acc |= 1<<(bit-1)
    return chr(BRAILLE_BASE + acc)

def lerp(a,b,t): return a+(b-a)*t
def ease_in_out(t): return 0.5 - 0.5*math.cos(math.pi*t)

def canvas_to_braille(buf_w, buf_h, sampler):
    # sampler(x,y)-> intensity 0..1 ; pack 2x4 cells into 1 char
    out = []
    for cy in range(0, buf_h, 4):
        row=[]
        for cx in range(0, buf_w, 2):
            pts=[]
            for y in range(4):
                for x in range(2):
                    ix,iy = cx+x, cy+y
                    if ix>=buf_w or iy>=buf_h: continue
                    if sampler(ix,iy) > 0.5:
                        pts.append((x,y))
            ch = braille_from_points(pts) if pts else " "
            row.append(ch)
        out.append("".join(row))
    return "\n".join(out)

def canvas_to_blocks(buf_w, buf_h, sampler):
    """Convert canvas to half-block characters for better contrast"""
    out = []
    for cy in range(0, buf_h, 2):
        row = []
        for cx in range(buf_w):
            top = sampler(cx, cy) if cy < buf_h else 0
            bottom = sampler(cx, cy + 1) if cy + 1 < buf_h else 0
            
            if top > 0.7 and bottom > 0.7:
                char = "█"  # full block
            elif top > 0.7:
                char = "▀"  # upper half
            elif bottom > 0.7:
                char = "▄"  # lower half
            elif top > 0.3 or bottom > 0.3:
                char = "░"  # light shade
            else:
                char = " "
            
            row.append(char)
        out.append("".join(row))
    return "\n".join(out)

def draw_line(start_x, start_y, end_x, end_y, canvas, value=1.0):
    """Draw a line on a 2D canvas using Bresenham's algorithm"""
    dx = abs(end_x - start_x)
    dy = abs(end_y - start_y)
    sx = 1 if start_x < end_x else -1
    sy = 1 if start_y < end_y else -1
    err = dx - dy
    
    x, y = start_x, start_y
    
    while True:
        if 0 <= x < len(canvas[0]) and 0 <= y < len(canvas):
            canvas[y][x] = value
        
        if x == end_x and y == end_y:
            break
            
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy

def draw_circle(center_x, center_y, radius, canvas, value=1.0):
    """Draw a circle on a 2D canvas"""
    for y in range(len(canvas)):
        for x in range(len(canvas[0])):
            distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            if abs(distance - radius) < 0.5:
                canvas[y][x] = value

def flood_fill(canvas, start_x, start_y, target_value, fill_value):
    """Flood fill algorithm for canvas manipulation"""
    if (start_x < 0 or start_x >= len(canvas[0]) or 
        start_y < 0 or start_y >= len(canvas) or
        canvas[start_y][start_x] != target_value):
        return
    
    stack = [(start_x, start_y)]
    
    while stack:
        x, y = stack.pop()
        if (x < 0 or x >= len(canvas[0]) or 
            y < 0 or y >= len(canvas) or
            canvas[y][x] != target_value):
            continue
            
        canvas[y][x] = fill_value
        
        # Add neighbors to stack
        stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])