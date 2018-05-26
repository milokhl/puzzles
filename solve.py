# Solving Martin's Menace

import math
import numpy as np
from matplotlib import pyplot as plt
from shapely.geometry import box, Polygon
from shapely.affinity import translate, rotate
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch

class Piece(object):
	def __init__(self, poly):
		self.valid_poses = [] # (x, y, theta) that fit on board.
		self.original = poly
		self.polygon = poly

	def transform(self, pose):
		"""
		Applies the given pose to the ORIGINAL polygon.
		"""
		self.polygon = translate(self.original, xoff=pose[0], yoff=pose[1])
		self.polygon = rotate(self.polygon, pose[2], use_radians=True)

class Board(object):
	def __init__(self, width = 147.32, height = 96.52):
		self.width = width # mm
		self.height = height # mm
		self.pieces = [] # Piece objects.
		self.poses = [] # (x, y, theta)
		self.boundary = box(0, 0, self.width, self.height)

		fig = plt.figure()
		ax = fig.add_subplot(111)
		ax.set_xlim(0, self.width)
		ax.set_ylim(0, self.height)
		ax.set_aspect(1)
		self.fig = fig
		self.ax = ax
		plt.title("Board")

	def __repr__(self):
		rstr = "Poses:"
		for p in self.poses:
			rstr += " " + str(p)
		return rstr

	def plot(self, dt=0.001):
		patches = []
		colors = ['red', 'blue', 'green', 'yellow']
		patches.append(PolygonPatch(self.boundary, fc='gray'))
		for idx, piece in enumerate(self.pieces):
			patches.append(PolygonPatch(piece.polygon, fc=colors[idx], ec='#555555', lw=0.2, alpha=1, zorder=1))

		self.ax.add_collection(PatchCollection(patches, match_original=True))
		plt.pause(dt)

	def place(self, piece, pose, allow_overlap=False):
		"""
		Tries to place piece at given pose on the board. If succesful, the board
		is updated and True is returned. Otherwise nothing happens, and False is
		returned.
		piece: (Piece)
		pose: (x, y, theta)
		Returns: (bool) Whether the piece could be placed at pose.
		"""
		allowed = True
		piece.transform(pose)

		if not self.boundary.contains(piece.polygon):
			allowed = False
		else:
			for other in self.pieces:
				if piece.polygon.overlaps(other.polygon):
					allowed = False
					break

		# Add the transformed piece to the board.
		if allowed or allow_overlap:
			self.pieces.append(piece)
			self.poses.append(pose)
		return allowed

	def clear(self, ii):
		"""
		Clears the pieces such that all pieces from 0 to ii remain.
		For example, clear(1) will remove all pieces except for the first two.
		"""
		if (ii+1) < len(self.pieces):
			self.pieces = self.pieces[:ii+1]
			self.poses = self.poses[:ii+1]


def solve(pieces):
	board = Board()

	# Create pose discretization.
	xs = np.linspace(0, board.width, 10) # mm resolution.
	ys = np.linspace(0, board.height, 10) # mm resolution.
	thetas = np.linspace(0, 2*math.pi, 20) # 1 deg resolution.

	poses_all = []
	for x in xs:
		for y in ys:
			for t in thetas:
				poses_all.append((x, y, t))

	print('Made all poses!')

	poses_q1 = []
	for x in xs[:len(xs)//2]:
		for y in ys[:len(ys)//2]:
			for t in thetas:
				poses_q1.append((x, y, t))

	print('Made poses in quadrant!')

	P0, P1, P2, P3 = pieces

	for pose0 in poses_q1:
		# print('Pose0:', pose0)
		# Place P0 (only need to consider a single quadrant).
		board.clear(-1)
		success0 = board.place(P0, pose0, allow_overlap=True)

		board.plot()

		if success0:
			# Place P1.
			for pose1 in poses_all:
				# print('Pose1:', pose1)
				board.clear(0)
				success1 = board.place(P1, pose1, allow_overlap=True)

				board.plot()

				if success1:
					# Place P2.
					for pose2 in poses_all:
						success2 = board.place(P2, pose2, allow_overlap=True)

						board.clear(1)

						if success2:
							# Place P3.
							for pose3 in poses_all:
								board.clear(2)
								success3 = board.place(P3, pose3, allow_overlap=True)

								board.plot()

								if success3: # Win!
									return (True, board)

	return (False, None)

def example():
	b = Board()
	p1 = Polygon([(0, 0), (12, 12), (12, 0)])
	p2 = Polygon([(50, 70), (50, 90), (90, 90), (90, 70)])
	r1 = b.place(Piece(p1), (0, 0, 0))
	r2 = b.place(Piece(p2), (0, 0, 0))
	print(r1, r2)
	b.plot()


if __name__ == '__main__':
	# example()
	u = 19.05

	poly1 = Polygon([
		(0, 0), (u, 0), (u, u), (4*u, u), (4*u, 2*u),
		(3*u, 2*u), (3*u, 3*u), (2*u, 3*u), (2*u, 2*u), (0, 2*u)
	])

	poly2 = Polygon([
		(0, 0), (4*u, 0), (4*u, u), (3*u, u), (3*u, 2*u),
		(2*u, 2*u), (2*u, u), (0, u) 
	])

	poly3 = Polygon([
		(0, 0), (3*u, 0), (3*u, u), (2*u, u), (2*u, 3*u),
		(u, 3*u), (u, u), (0, u)
	])

	poly4 = Polygon([
		(0, 0), (2*u, 0), (2*u, 2*u), (3*u, 2*u), (3*u, 3*u),
		(u, 3*u), (u, u), (0, u)
	])

	pieces = [Piece(poly1), Piece(poly2), Piece(poly3), Piece(poly4)]

	# b = Board()
	# b.place(Piece(poly4), (0, 0, 0))
	# b.plot()

	success, final_board = solve(pieces)

	if success:
		print('SUCCESS!')
		print(final_board)
		final_board.plot()
	else:
		print('NONE FOUND')
