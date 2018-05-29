# Solving Martin's Menace

import math, time, json
import numpy as np
from matplotlib import pyplot as plt
from shapely.geometry import box, Polygon
from shapely.affinity import translate, rotate
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch

class Piece(object):
	def __init__(self, poly):
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

	def save(self):
		savedict = {
			'width': self.width,
			'height': self.height,
			'pieces_tf': [str(piece.polygon) for piece in self.pieces],
			'poses': self.poses
		}
		with open('board.json', 'w') as f:
			f.write(json.dumps(savedict, indent=2))

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


def solve(pieces, plot=False, print_lvl=0):
	P0, P1, P2, P3 = pieces

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

	print('[INFO] Made all poses: %d!' % len(poses_all))

	poses_q1 = []
	for x in xs[:len(xs)//2]:
		for y in ys[:len(ys)//2]:
			for t in thetas:
				poses_q1.append((x, y, t))

	# Precompute allowed poses for each piece (inside of the board).
	valid_poses = {}
	for i, P in enumerate(pieces):
		if i not in valid_poses: valid_poses[i] = []
		for pose in poses_all:
			P.transform(pose)
			if board.boundary.contains(P.polygon):
				valid_poses[i].append(pose)
		print('[INFO] Valid for piece %d: %d' % (i, len(valid_poses[i])))

	poses_q1_valid = []
	for pose in poses_q1[:]:
		P0.transform(pose)
		if board.boundary.contains(P0.polygon):
			poses_q1_valid.append(pose)
	print('[INFO] Valid for P0 in Q1: %d' % len(poses_q1_valid))

	total_config = len(poses_q1_valid) * len(valid_poses[1]) * len(valid_poses[2]) * len(valid_poses[3])
	print('[INFO] Possible configurations: %d' % total_config)

	last_time_P0 = time.time()
	for idx0, pose0 in enumerate(poses_q1_valid):
		# Place P0 (only need to consider a single quadrant).
		if print_lvl >= 0: print('[PROGRESS] Trying pose %d/%d for P0. (last=%f sec)' % \
			(idx0, len(poses_q1_valid), time.time() - last_time_P0))
		last_time_P0 = time.time()
		board.clear(-1)
		success0 = board.place(P0, pose0, allow_overlap=True)
		if plot: board.plot()

		if success0:
			# Place P1.
			for idx1, pose1 in enumerate(valid_poses[1]):
				if print_lvl >= 1: print('[PROGRESS] Trying pose %d/%d for P1.' % (idx1, len(valid_poses[1])))
				board.clear(0)
				success1 = board.place(P1, pose1, allow_overlap=True)
				if plot: board.plot()

				if success1:
					# Place P2.
					for idx2, pose2 in enumerate(valid_poses[2]):
						if print_lvl >= 2: print('[PROGRESS] Trying pose %d/%d for P2.' % (idx2, len(valid_poses[2])))
						board.clear(1)
						success2 = board.place(P2, pose2, allow_overlap=True)
						if plot: board.plot()

						if success2:
							board.save()
							# Place P3.
							for idx3, pose3 in enumerate(valid_poses[3]):
								if print_lvl >= 3: print('[PROGRESS] Trying pose %d/%d for P3.' % (idx3, len(valid_poses[3])))
								board.clear(2)
								success3 = board.place(P3, pose3, allow_overlap=True)
								if plot: board.plot()

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

	success, final_board = solve(pieces)

	if success:
		print('SUCCESS!')
		print(final_board)
		final_board.plot()
		plt.show()
	else:
		print('NONE FOUND')
