import heapq
import time
import pygame

class Cell(object):
    def __init__(self, x, y, reachable):
        """
        Initialize new cell

        @param x cell x coordinate
        @param y cell y coordinate
        @param reachable is cell reachable? not a wall?
        """
        self.reachable = reachable
        self.x = x
        self.y = y
        self.parent = None
        self.g = 0
        self.h = 0
        self.f = 0


class AStar(object):
    def __init__(self):
        self.opened = []
        heapq.heapify(self.opened)
        self.closed = set()
        self.cells = []
        self.grid_height = 60
        self.grid_width = 80


    def init_grid(self, width, height, screen, start, end):
        """Prepare grid cells, walls.

        @param width grid's width.
        @param height grid's height.
        @param screen pygame frame
        @param start grid starting point x,y tuple.
        @param end grid ending point x,y tuple.
        """
        self.grid_height = height
        self.grid_width = width
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                if screen.get_at((x, y))[0] > 0:
                    reachable = False
                else:
                    reachable = True
                self.cells.append(Cell(x, y, reachable))
        self.start = self.get_cell(*start)
        self.end = self.get_cell(*end)

    def get_heuristic(self, cell):
        """Compute the heuristic value H for a cell.

        Distance between this cell and the ending cell multiply by 10.

        @returns heuristic value H
        """
        return 10 * (abs(cell.x - self.end.x) + abs(cell.y - self.end.y))


    def get_cell(self, x, y):
        """Returns a cell from the cells list.

        @param x cell x coordinate
        @param y cell y coordinate
        @returns cell
        """
        return self.cells[x * self.grid_height + y]


    def get_adjacent_cells(self, cell):
        """Returns adjacent cells to a cell.

        Clockwise starting from the one on the right.

        @param cell get adjacent cells for this cell
        @returns adjacent cells list.
        """
        cells = []
        if cell.x < self.grid_width-1:
            cells.append(self.get_cell(cell.x+1, cell.y))
        if cell.y > 0:
            cells.append(self.get_cell(cell.x, cell.y-1))
        if cell.x > 0:
            cells.append(self.get_cell(cell.x-1, cell.y))
        if cell.y < self.grid_height-1:
            cells.append(self.get_cell(cell.x, cell.y+1))
 
        #diagonals
        if cell.x < self.grid_width-1 and cell.y < self.grid_height-1:
            cells.append(self.get_cell(cell.x+1, cell.y+1))
        if cell.x > 0 and cell.y > 0:
            cells.append(self.get_cell(cell.x-1, cell.y-1))
        if cell.x > 0 and cell.y < self.grid_height-1:
            cells.append(self.get_cell(cell.x-1, cell.y+1))
        if cell.x < self.grid_width-1 and cell.y > 0:
            cells.append(self.get_cell(cell.x+1, cell.y-1))

        return cells


    def get_path(self):
        cell = self.end
        path = [(cell.x, cell.y)]
        while cell.parent is not self.start:
            cell = cell.parent
            path.append((cell.x, cell.y))

        path.append((self.start.x, self.start.y))
        path.reverse()
        return path


    def update_cell(self, adj, cell):
        """Update adjacent cell.

        @param adj adjacent cell to current cell
        @param cell current cell being processed
        """
        adj.g = cell.g + 10
        adj.h = self.get_heuristic(adj)
        adj.parent = cell
        adj.f = adj.h + adj.g


    def solve(self):
        """Solve maze, find path to ending cell.

        @returns path or None if not found.
        """
        # add starting cell to open heap queue
        heapq.heappush(self.opened, (self.start.f, self.start))
        while len(self.opened):
            # pop cell from heap queue
            f, cell = heapq.heappop(self.opened)
            # add cell to closed list so we don't process it twice
            self.closed.add(cell)
            # if ending cell, return found path
            if cell is self.end:
                return self.get_path()
            # get adjacent cells for cell
            adj_cells = self.get_adjacent_cells(cell)
            for adj_cell in adj_cells:
                if adj_cell.reachable and adj_cell not in self.closed:
                    if (adj_cell.f, adj_cell) in self.opened:
                        # if adj cell in open list, check if current path is
                        # better than the one previously found
                        # for this adj cell.
                        if adj_cell.g > cell.g + 10:
                            self.update_cell(adj_cell, cell)
                    else:
                        self.update_cell(adj_cell, cell)
                        # add adj cell to open list
                        heapq.heappush(self.opened, (adj_cell.f, adj_cell))



# bresenham as of http://eugen.dedu.free.fr/projects/bresenham/
def getVisionLine (x1, y1, x2, y2):

    dx = x2 - x1; 
    dy = y2 - y1; 

    xsign = 1 if dx > 0 else -1
    ysign = 1 if dy > 0 else -1

    dx = abs(dx)
    dy = abs(dy)

    if dx > dy:
        xx, xy, yx, yy = xsign, 0, 0, ysign
    else:
        dx, dy = dy, dx
        xx, xy, yx, yy = 0, ysign, xsign, 0

    D = 2*dy - dx
    y = 0

    for x in range(dx + 1):
        yield x1 + x*xx + y*yx, y1 + x*xy + y*yy
        if D > 0:
            y += 1
            D -= dx
        D += dy



def smoothPath(scaled, path):
    start = 0
    next = 1
    end = len(path) -1
    while next < len(path)-1:

        blocked = False
        for cell in getVisionLine(path[start][0], path[start][1], path[next][0], path[next][1]):
            if scaled.get_at(cell)[0] > 0:    # cell blocked
                blocked = True

        # if we hit a blocked cell add a waypoint to the list
        if blocked:
            #path.insert(next, path[next])
            start = next
            next = start+1

        # if direct path is free remove the waypoint
        else:
            del path[next]
            



def findPath(screen, source, target, scaler):
    '''
    @screen is a 640*480 image
    @source is the cam location
    @target is the point we want to go
    @scaler is the reduction factor for the path search grid
    '''
    start_time = time.time()
    finderGrid =  (screen.get_width()/scaler, screen.get_height()/scaler)
    scaled = pygame.transform.scale(screen,finderGrid)
    scaledSource = [x/8 for x in source]
    scaledTarget = [x/8 for x in target]
    a = AStar()
    a.init_grid(scaled.get_width(), scaled.get_height(), scaled, scaledSource, scaledTarget)
    path = a.solve()

    print("path found in %s seconds " % (time.time() - start_time))

    if path==None:
        print "no path found "
        return
    else:
        for i in range(0, len(path) - 1):
            point = [x * 8 for x in path[i]]
            map.circle(BRIGHTGREEN, point, 4)
            map.save("astarPath.png")

        smoothPath(scaled, path)

        for i in range(0, len(path) - 1):
            cellFrom = [x * 8 for x in path[i]]
            cellTo = [x * 8 for x in path[i+1]]
            map.line(BRIGHTGREEN, cellFrom, cellTo, 1)
            map.save("directPath.png")

    # angle of first path segment of a  straight forward looking robot
    # tan(xdiff/ydiff)
    dx = path[0][0] - path[1][0]
    dy = path[0][1] - path[1][1]
    angle = np.degrees(np.tan(float(dx) / -dy))
    dist = np.sqrt(pow(dx, 2) + pow(dy, 2))
    dir = MOVEMENT.VORWAERTS         # at the moment we rotate and drive forward only

    print "action rotate angle: ", dir, " speed: 100"
    arduino.sendRotateCommand(dir)

    if dist > 500:
        speed = 255
    elif dist > 200:
        speed = 180
    else: 
        speed = 150

    print "action move forward, speed: ", speed
    #arduino.sendMoveCommand(0, speed)
