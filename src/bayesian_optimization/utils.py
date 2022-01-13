import numpy as np
from matplotlib import pyplot as plt
from pylab import *


def plot_3d_boundary(X, Y, mesh_X, mesh_Y,
                     mu_plot, var_plot,
                     elev,
                     angle,
                     z_lims,
                     plot_new=False,
                     new_X=None,
                     new_Y=None,
                     plot_ci=True,
                     title=None,
                     save_fig_path=None):

    fig = plt.figure(figsize=(10, 10), dpi=100)
    ax = fig.gca(projection='3d')
    surf = ax.plot_surface(mesh_X, mesh_Y, mu_plot.reshape(
        (1000, 21)), cmap='viridis', linewidth=0, antialiased=False, alpha=0.60)

    if plot_ci:
        surf_var = ax.plot_surface(mesh_X, mesh_Y, (mu_plot-var_plot).reshape(
            (1000, 21)), cmap='viridis', linewidth=0, antialiased=False, alpha=0.20)
        surf_var = ax.plot_surface(mesh_X, mesh_Y, (mu_plot+var_plot).reshape(
            (1000, 21)), cmap='viridis', linewidth=0, antialiased=False, alpha=0.20)

    ax.scatter(X[:, 0].flatten(), X[:, 1].flatten(), Y.flatten(),
               s=100, marker="o", color="b", label="Initial observations")

    if plot_new:
        ax.scatter(new_X[:, 0].flatten(), new_X[:, 1].flatten(),
                   new_Y.flatten(), marker="x", color="r", label="All observations", s=100)

    ax.grid(True)
    ax.set_xlabel("Num batteries")
    ax.set_ylabel("Battery capacity")
    ax.set_zlabel("Cumulative reward")

    if z_lims:
        ax.set_zlim(z_lims)

    if title:
        plt.title(title)
    plt.legend(loc='upper right', prop={'size': 15})

    if save_fig_path:
        # for angle in range(0, 360, 40):
        #     ax.view_init(elev=10., azim=angle)
        plt.savefig(save_fig_path)

    ax.view_init(elev=elev, azim=angle)
    return fig, ax


def plot_3d_observed_rewards(X, Y,
                             elev,
                             angle,
                             z_lims,
                             new_X=None,
                             new_Y=None,
                             title=None,
                             save_fig_path=None):

    fig = plt.figure(figsize=(10, 10), dpi=100)
    ax = plt.axes(projection='3d')

    im = ax.plot_trisurf(new_X[:, 0].flatten(), new_X[:, 1].flatten(
    ), new_Y.flatten(), cmap='viridis', alpha=0.70)

    ax.scatter(X[:, 0].flatten(), X[:, 1].flatten(), Y.flatten(),
               s=100, marker="o", color="b", label="Initial observations")
    ax.scatter(new_X[:, 0].flatten(), new_X[:, 1].flatten(),
               new_Y.flatten(), marker="x", color="r", label="All observations", s=100)

    min_X = new_X[np.argmin(new_Y)]
    min_Y = np.min(new_Y)
    ax.scatter(min_X[0], min_X[1], min_Y, c='black',
               marker='D', label="Minimum", s=200)

    ax.legend(loc=1, prop={'size': 15})
    ax.set_xlabel("Num batteries")
    ax.set_ylabel("Battery capacity")
    ax.set_zlabel("Cumulative reward")

    ax.view_init(elev=elev, azim=angle)

    if z_lims:
        ax.set_zlim(z_lims)

    ax.grid(True)
    plt.title("Contour of observed rewards")

    if save_fig_path:
        # for angle in range(0, 360, 40):
        #     ax.view_init(elev=10., azim=angle)
        plt.savefig(save_fig_path)

    return fig, ax
