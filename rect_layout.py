import math
from copy import copy
math.tau = math.pi*2
default_precision = 2

def frange(end, jump):
  x = 0
  while x < end:
    yield x
    x += jump

def defp(val, p):
  try:
    return [defp(v, p) for v in val]
  except TypeError:
    return round(val, p)

class Rayish:
  def __init__(self, angle_or_end, origin = (0,0), length=1, precision = default_precision):
    self.p = precision
    self.origin = defp(origin, self.p)
    try:
      self.end = angle_or_end
      self.angle = self.clamp_range(
        math.atan2(
          self.end[1] - self.origin[1],
          self.end[0] - self.origin[0]
        )
      )
    except TypeError:
      self.angle = angle_or_end
      self.end = (
        self.origin[0] + math.cos(self.angle)*length,
        self.origin[1] + math.sin(self.angle)*length
      )

    self.end = defp(self.end, self.p)
    self._length = None

  @staticmethod
  def as_pi(val):
    try:
      return [Rayish.as_pi(v) for v in val]
    except TypeError:
      return "{}π".format(round(val/math.pi, 3))

  @staticmethod
  def clamp_range(val, range=(0,2*math.pi)):
    if not (range[1] - range[0]) == 2*math.pi:
      raise ValueError("Range must span 2*pi")

    while val < range[0]:
      val += 2*math.pi
    while val > range[1]:
      val -= 2*math.pi

    return val

  def __str__(self):
    return "Rayish length {} from {} to {} (angle {})".format(
      self.length(), self.origin, self.end, self.as_pi(self.angle)
    )

  def draw(self, canvas, tags = None, color="red"):
    if(canvas):
      elms = []
      oval_size = 5
      elms.append(canvas.create_line(
        self.origin[0], self.origin[1],
        self.end[0], self.end[1],
        dash=(1,2),
        tags=tags
      ))
      elms.append(canvas.create_oval(
        self.end[0]-oval_size/2, self.end[1]-oval_size/2,
        self.end[0]+oval_size/2, self.end[1]+oval_size/2,
        fill=color, tags=tags
      ))
      return elms
    return None

  def distance(self, angle):
    phi = math.abs(angle.angle - self.angle) % 360
    distance = 360 - phi if phi > 180 else phi
    return distance

  def length(self):
    if not self._length:
      self._length = math.sqrt(
        math.pow((self.origin[0] - self.end[0]), 2) +
        math.pow((self.origin[1] - self.end[1]), 2)
      )

    return self._length

  def intersects_segment(self, a, b):
    xdiff = (a[0] - b[0], self.origin[0] - self.end[0])
    ydiff = (a[1] - b[1], self.origin[1] - self.end[1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
      return None

    d = (det(a, b), det(self.origin, self.end))
    x = round(det(d, xdiff) / div, 3)
    y = round(det(d, ydiff) / div, 3)

    print(x, y)

    x_range = [
      math.floor(min(a[0],b[0])),
      math.ceil(max(a[0],b[0]))
    ]
    y_range = [
      math.floor(min(a[1],b[1])),
      math.ceil(max(a[1],b[1]))
    ]

    print(x_range, y_range)

    if x >= x_range[0] and x <= x_range[1] and y >= y_range[0] and y <= y_range[1]:
      return (x, y)
    else:
      return None

class Rect:
  def __init__(self, size, center = (0,0), precision = default_precision):
    self.p = precision
    self.size = defp(size, self.p)
    self.move_to(center)

  def __str__(self):
    return "Rectangle: tldr {}/{}/{}/{}".format(
      *[round(v, 3) for v in (self.top, self.left, self.bottom, self.right)]
    )

  def move(self, dist):
    print("Moving {} from {} ".format(dist, self.center))
    self.move_to((
      self.center[0] + dist[0],
      self.center[1] + dist[1]
    ))

  def move_to(self, center):
    self.center = defp(center, self.p)
    print("New center: {}".format(self.center))

    self.left = defp(self.center[0] - self.size[0]/2, self.p)
    self.right = defp(self.center[0] + self.size[0]/2, self.p)
    self.bottom = defp(self.center[1] - self.size[1]/2, self.p)
    self.top = defp(self.center[1] + self.size[1]/2, self.p)

  def corners(self):
    return [
      (self.right, self.top),
      (self.left, self.top),
      (self.left, self.bottom),
      (self.right, self.bottom)
    ]

  def corner_angles(self, origin = (0,0)):
    return [
      Rayish(c, origin).angle
      for c in self.corners()
    ]

  def corner_distances(self, angle, origin=(0,0)):
    corner_angles = self.corner_angles()
    distances = [ca - angle for ca in corner_angles]
    print(Rayish.as_pi(distances))
    distances = [Rayish.clamp_range(d, [-math.pi, math.pi]) for d in distances]
    return distances

  def intersects_angle(self, angle, origin = (0,0)):
    distances = self.corner_angles(origin)
    return (min(distances) < 0 and max(distances) > 0)

  def outer_radius(self, angle):
    print(self)

    # We can ignore the closest corner
    # Line will then be between two of the remaining points
    ignore_corner = self.get_ignore(angle)
    middle_corner = (ignore_corner + 2) % 4
    distances = self.corner_distances(angle)
    dist_middle = distances[middle_corner]

    print("Finding sides for angle {}, ignoring corner {}, middle corner {} ({})".format(
      Rayish.as_pi(angle), ignore_corner, middle_corner, Rayish.as_pi(dist_middle)
    ))

    # Ensure our corner is even in the quadrant
    corner_angles = self.corner_angles()
    if (corner_angles[middle_corner] < middle_corner*math.pi/2 or
        corner_angles[middle_corner] > (middle_corner+1)*math.pi/2):
      return None

    print(Rayish.as_pi(distances))
    if not min(distances) < 0 and max(distances) > 0:
      return None

    ray = Rayish(angle)

    corners = self.corners()
    if(dist_middle < 0):
      point = ray.intersects_segment(corners[(middle_corner + 1) % 4], corners[middle_corner])
      side = (middle_corner + 1) % 4
    else:
      point = ray.intersects_segment(corners[(middle_corner - 1) % 4], corners[middle_corner])
      side = middle_corner

    if not point:
      return None

    ray = Rayish(point)
    ray.side = side
    print(ray)
    return ray

  def get_ignore(self, angle):
    quadrant = math.floor(angle/(math.pi/2))
    return int((quadrant + 2) % 4)

  def intersects(self, rect):
    # standard cartesian
    # "below" is <
    # "above" is >
    #print(rect)
    #print(self)
    v = False
    if rect.top < self.top:
      if rect.top > self.bottom:
        v = True
    else:
      if rect.bottom < self.top:
        v = True

    h = False
    if rect.left > self.left:
      if rect.left < self.right:
        h = True
    else:
      if rect.right > self.left:
        h = True

    intersects = (v and h)
    if(intersects):
      print("Intersection:\n{}\n{}".format(self, rect))
    return (v and h)

  def draw(self, canvas, tags = None, color = "black"):
    if(canvas):
      elms = []
      elms.append(canvas.create_rectangle(
        self.left, self.top,
        self.right, self.bottom,
        tags = tags,
        outline = color
      ))
      return elms
    return None


class Layout:
  def __init__(self, num_slices, canvas = None, margin = 0.05, precision = default_precision):
    self.rects = []
    self.outer_rects = {}
    self.angle = 0
    self.num_slices = num_slices
    self.angle_step = math.tau/num_slices
    self.canvas = canvas
    self.margin = margin

  def add_rect(self, size):
    if(len(self.rects) == 0):
      rect = Rect(size, (0,0))
    else:
      rect = self.place_rect(size)

    if rect is None:
      print("Couldn't add rectangle!")
      return

    rect.draw(self.canvas)

    self.rects.append(rect)
    return rect

  def get_radius(self, angle):
    try:
      outer_rect_idx = self.outer_rects[angle]
    except KeyError:
      outer_rect_idx = 0

    max_radius = None
    for i in reversed(range(len(self.rects))):
      cur_radius = self.rects[i].outer_radius(angle)
      if cur_radius and (max_radius is None or cur_radius.length() > max_radius.length()):
        new_outer = i
        max_radius = copy(cur_radius)

    self.outer_rects[angle] = new_outer

    return max_radius

  def intersects_any(self, rect):
    for r in reversed(self.rects):
      if r.intersects(rect):
        return True

  def place_rect(self, size):
    min_radius = None
    rect = Rect(size)
    if(self.canvas):
      self.canvas.delete("outer_radius")

    radii = []
    for ang in frange(math.tau, self.angle_step):
      print("---")
      print("Getting radius for angle {}".format(Rayish.as_pi(ang)))
      base_radius = self.get_radius(ang)
      radii.append(base_radius)

    radii.sort(key = lambda x: x.length())

    hexcolor = lambda tup: '#%02x%02x%02x' % tuple(tup)
    curcolor = [255, 0, 0]
    color_inc = int(192/self.num_slices)

    for r in radii:
      r.draw(self.canvas, tags="outer_radius", color = hexcolor(curcolor))
      curcolor[0] -= color_inc

    # Try just side-scooting
    for r in radii:
      # Move rectangle so edge is on radius end
      axis = r.side % 2
      direction = 1-int(r.side/2)*2
      move_dist = [0,0]
      move_dist[axis] = direction*size[axis]/2*(1+self.margin)

      rect.move_to(r.end)
      rect.move(move_dist)

      # If we're good here, that's as good as we'll get
      if not self.intersects_any(rect):
        return rect

      # Otherwise, scoot around until we find something better
      # Scoot from inside out
      nudge_pos = [0,0]
      nudge_neg = [0,0]
      nudge_pos[1-axis] = size[1-axis]/(self.num_slices/2)
      nudge_neg[1-axis] = -size[1-axis]/(self.num_slices/2)

      rect_pos = copy(rect)
      rect_neg = copy(rect)
      curcolor = [0, 255, 0]
      if(self.canvas):
        self.canvas.delete("shifty")
      for nudge_step in range(1, int(self.num_slices/2)):
        # Shift positive
        rect_pos.move(nudge_pos)
        rect_pos.draw(self.canvas, tags="shifty", color = hexcolor(curcolor))
        if not self.intersects_any(rect_pos):
          return rect_pos

        rect_neg.move(nudge_neg)
        rect_neg.draw(self.canvas, tags="shifty", color = hexcolor(curcolor))
        if not self.intersects_any(rect_neg):
          return rect_neg

        curcolor[1] -= color_inc*2

    return None

      #budge = 1
      #while True:
      #  for r in self.rects:
      #    if rect.intersects(r):
      #      rect.move(move_dist*budge)
      #      continue

      #  # At this point, we didn't intersect
      #  # Let's move closer
      #  budge = -budge/2


