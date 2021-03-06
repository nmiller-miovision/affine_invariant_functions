from math import sqrt, atan2, cos, sin
import cv2
import numpy as np
import sys

def square_img_idx_to_coords(W, rowcol):
    row, col = rowcol
    x = 2.*col/(W-1.) - 1.
    y = -2.*row/(W-1.) + 1.
    return np.array([[x], [y]])

def coords_to_square_img_idx(W, xy):
    x = xy[0,0]
    y = xy[1,0]
    row = int((-y + 1)/2.*(W-1))
    col = int((x + 1)/2.*(W-1))
    return row, col

def kernel_read(k, x):
    """
        x, y in -1, 1 on plot surface translating to 0, cols x 0, rows 
    """
    W,W,n = k.shape
    row, col = coords_to_square_img_idx(W, x)
    return k[row,col,:]

class AffineInvariantRecUnitSqFunction:
    def __init__(self, A, b, k, W):
        self.A = A
        self.Ainv = np.linalg.inv(A)
        self.b = b
        self.k = k
        rows, cols, n = self.k.shape
        assert rows == cols
        self.W = W
        self.Dmask = np.zeros((self.W, self.W), dtype=np.uint8)
        self._populate_dmask()

    def __call__(self, x):
        if x[0,0] < -1 or x[0,0] > 1 or x[1,0] < -1 or x[1,0] > 1:
            return (0,0,0)
        if self.in_D(x):
            return kernel_read(self.k, x)
        else:
            f = self
            return f(np.dot(self.Ainv, (x - self.b)))

    def in_D(self, x):
        row, col = coords_to_square_img_idx(self.W, x)
        return self.Dmask[row, col] > 0

    def _populate_dmask(self):
        self.Dmask[:,:] = 255
        for row in range(self.W):
            for col in range(self.W):
                x = square_img_idx_to_coords(self.W, (row, col))
                inv = np.dot(self.Ainv, x-self.b)
                if -1. <= inv[0,0] <= 1. and -1. <= inv[1,0] <= 1.:
                    self.Dmask[row, col] = 0
                

def populate_large(large, f, A, b):
    W = f.W
    for row in range(W):
        for col in range(W):
            x = square_img_idx_to_coords(W, (row, col))
            x = np.dot(A, x) + b
            large[row, col, :] = f(x)


def A_b_from_params(angle, scale, b, b_scale):
        A = np.array([[cos(angle), -sin(angle)], [sin(angle), cos(angle)]])*scale
        return A, b * b_scale

def main(args):
    ifile = "sisters_squared.png"
    sq = cv2.imread(ifile)
    assert sq.shape[0] == sq.shape[1]
    W,W,n = sq.shape
    P = square_img_idx_to_coords(W, (875, 2152))
    Q = square_img_idx_to_coords(W, (1416, 3337))
    M = np.array([[-1,-1, 1, 0],
                  [ 1,-1, 0, 1],
                  [ 1,-1, 1, 0],
                  [ 1, 1, 0, 1]])
    params = np.dot(np.linalg.inv(M), np.array([P[0],P[1],Q[0],Q[1]]))
    us = params[0, 0]
    vs = params[1, 0]
    c = params[2, 0]
    d = params[3, 0]
    A = np.array([[us, -vs], [vs, us]])
    u = A[0,0]
    v = A[1,0]
    s = np.sqrt(u*u + v*v)
    Theta = atan2(v, u)
    print(Theta)
    b_final = np.array([[c],[d]])
    b = b_final
    f = AffineInvariantRecUnitSqFunction(A, b, sq, 3338)
    del b
    large = np.zeros((f.W,f.W,n), dtype=sq.dtype)
    angle = 0.
    scale = 1.
    b_scale = 0.
    frame = 0

    A, b = A_b_from_params(angle, scale, b_final, b_scale)
    populate_large(large, f, A, b)
    cv2.imwrite(f"magic.png", large)
    sys.exit(0)
    while frame < 2:
        cv2.imwrite(f"smooth_affine_rec{frame}.png", large)
        frame += 1
    u = 0
    while scale > 0.8:
        A, b = A_b_from_params(0, scale, b_final, 0)
        populate_large(large, f, A, b)
        cv2.imwrite(f"smooth_affine_rec{frame}.png", large)
        scale -= (1-0.8)/5.
        frame += 1
        
    while u <= 1.:
        A, b = A_b_from_params(u * Theta, 0.8 * (1. - u) + s * u, b_final, u)
        populate_large(large, f, A, b)
        cv2.imwrite(f"smooth_affine_rec{frame}.png", large)
        u += .05
        frame += 1
    sys.exit(0)


    while scale > s:
        A, b = A_b_from_params(angle, scale, b_final, b_scale)
        populate_large(large, f, A, b)
        cv2.imwrite(f"affine_rec{frame}.png", large)
        scale -= (1. - s)/10.
        frame += 1

    sys.exit(0)
    while scale > s:
        A, b = A_b_from_params(angle, scale, b_final, b_scale)
        populate_large(large, f, A, b)
        cv2.imwrite(f"affine_rec{frame}.png", large)
        scale -= (1. - s)/10.
        frame += 1
    scale = s
    A, b = A_b_from_params(angle, scale, b_final, b_scale)
    populate_large(large, f, A, b)
    cv2.imwrite(f"affine_rec{frame}.png", large)
    while abs(angle) < abs(Theta):
        A, b = A_b_from_params(angle, scale, b_final, b_scale)
        populate_large(large, f, A, b)
        cv2.imwrite(f"affine_rec{frame}.png", large)
        angle += Theta / 8.
        frame += 1
    while b_scale < 1.:
        A, b = A_b_from_params(angle, scale, b_final, b_scale)
        populate_large(large, f, A, b)
        cv2.imwrite(f"affine_rec{frame}.png", large)
        b_scale += .1
        frame += 1
    b_scale = 1.
    A, b = A_b_from_params(angle, scale, b_final, b_scale)
    populate_large(large, f, A, b)
    cv2.imwrite(f"affine_rec{frame}.png", large)



if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))    
