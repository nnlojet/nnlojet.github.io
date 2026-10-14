import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.backends.backend_pdf import PdfPages
# from matplotlib.offsetbox import OffsetImage, AnnotationBbox
# import matplotlib.image as mpimg

# import matplotlib.font_manager as fm
# hack_path = "ttf/Hack-Regular.ttf"
# fm.fontManager.addfont(hack_path)
# plt.rcParams["font.family"] = "Hack"

plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif"
})

### Rebin histogram
def rebin(array, rebin=2, nx=3, ycol=3, ecol=4, xmin=-1e300, xmax=1e300):
    ilo = 0
    ihi = len(array[:,0])-1
    if (ihi < 1) : raise Error("number of bins must be >= 2")
    if   (nx == 1) : minslice = array[:,0]; maxslice = array[:,0]
    elif (nx == 3) : minslice = array[:,0]; maxslice = array[:,2]
    else : raise Error("nx is not 1 or 3")
    # get the bounds
    for i in range(len(minslice)):
        if (xmin <= minslice[i]): ilo = i; break;
    for i in range(len(minslice)-1,-1,-1):
        if (xmax >= maxslice[i]): ihi = i; break;
    # now figure out how many bins we're going to need
    nbins = int(ihi+1-ilo)//rebin
    #print ilo, ihi, minslice[ilo], maxslice[ihi]
    #print nbins
    rebinned = np.empty( (nbins, len(array[0,:])) )
    # and now do the rebinning
    ir = 0
    for i in range(ilo, ilo+nbins*rebin, rebin):
        # first handle the x axes
        if (nx == 1):
            rebinned[ir, 0] = sum(array[i:i+rebin,0])/rebin
        if (nx == 3):
            rebinned[ir, 0   ] = array[i        , 0    ]
            rebinned[ir, nx-1] = array[i+rebin-1, nx-1 ]
            rebinned[ir, 1]    = 0.5*(rebinned[ir,0]+rebinned[ir,2])
        # then the remaining ones
        rebinned[ir, ycol] = np.sum(array[i:i+rebin, ycol], axis=0) / rebin
        rebinned[ir, ecol] = np.sqrt(np.sum(np.square(array[i:i+rebin, ecol]), axis=0)) / rebin
        ir += 1
    return rebinned


def load_histogram(filename, nreb):
    raw = np.loadtxt(filename, comments="#")
    idxs = [3,5,7,9,11,13,15]

    ### Perform rebinning
    data = rebin(raw, rebin=nreb, nx=3, ycol=3, ecol=4)
    for col in idxs:
        tmparr = rebin(raw, rebin=nreb, nx=3, ycol=col, ecol=col+1)
        data[:,col] = tmparr[:,col]
        data[:,col+1] = tmparr[:,col+1]

    var_lower = data[:, 0]
    var_upper = data[:, 2]
    var_center = data[:, 1]

    scales = np.column_stack([data[:,ii] for ii in idxs])
    scale_errs = np.column_stack([data[:,ii+1] for ii in idxs])
    ### convert fb to pb
    scales /= 1e3
    scale_errs /= 1e3

    nominal = scales[:, 0]
    nominal_err = scale_errs[:, 0]
    scale_min = np.min(scales, axis=1)
    scale_max = np.max(scales, axis=1)
    return var_lower, var_upper, var_center, nominal, nominal_err, scale_min, scale_max


def plot_observable(obs_name, yscale, lat, unit, outfile, input_dir, nreb=1, xlims=None):
    #levels = ["lo", "nlo", "nnlo"]
    levels = ["LO", "NLO", "NNLO"]
    names = ["LO", "NLO", "NNLO"]
    colors = ["#2ca02c","blue","red"]
    hists = []
    for lvl in levels:
        fname = Path(input_dir) / f"{lvl}.{obs_name}.dat"
        hists.append(load_histogram(fname, nreb))

    all_lower = np.concatenate([h[0] for h in hists])
    all_upper = np.concatenate([h[1] for h in hists])
    x_min = np.min(all_lower)
    x_max = np.max(all_upper)

    fig, (ax_top, ax_bottom) = plt.subplots(
        2, 1, sharex=True, figsize=(4, 3),
        gridspec_kw={"height_ratios": [3, 1]}
    )
    # fig.subplots_adjust(left=0.15, right=0.95, bottom=0.15, top=0.99,
    #                     wspace=0.0, hspace=0.1)

    for name, color, h in zip(names, colors, hists):
        var_lower, var_upper, var_center, y_nom, y_err, y_min, y_max = h
        bin_edges = np.append(var_lower, var_upper[-1])
        ax_top.stairs(y_nom, bin_edges, label=name, color=color, lw=1.5, baseline=None)
        ax_top.stairs(y_max, bin_edges, baseline=y_min, fill=True, alpha=0.15, color=color)

    sunit = "/"+unit if unit != "" else ""
    ax_top.set_ylabel(r"$\mathrm{d}\sigma/\mathrm{d}$"+lat+" [pb"+sunit+"]")
    ax_top.legend(frameon=False)
    ax_top.grid(True, ls=":", alpha=0.5)
    ax_top.set_yscale(yscale)
    if xlims is None:
        ax_top.set_xlim(x_min, x_max)
    else:
        ax_top.set_xlim(xlims)

    ### add NNLOJET logo
    # img = mpimg.imread('nnlogo_col_nobkg.png')
    # imagebox = OffsetImage(img, zoom=0.05)  # zoom controls size
    # ab = AnnotationBbox(imagebox, (0.1, 0.2), frameon=False, xycoords='axes fraction')
    # ax_top.add_artist(ab)

    _, _, _, y_nom_ref, _, _, _ = hists[1]  # NLO reference

    all_ratios = []
    for name, color, h in zip(names, colors, hists):
        var_lower, var_upper, var_center, y_nom, y_err, y_min, y_max = h
        ratio_nom = y_nom / y_nom_ref
        ratio_err = y_err / y_nom_ref
        ratio_err_lo = (y_nom - y_err) / y_nom_ref
        ratio_err_hi = (y_nom + y_err) / y_nom_ref
        ratio_min = y_min / y_nom_ref
        ratio_max = y_max / y_nom_ref

        bin_edges = np.append(var_lower, var_upper[-1])
        ax_bottom.stairs(ratio_nom, bin_edges, color=color, lw=1.5, baseline=None)
        ax_bottom.stairs(ratio_max, bin_edges, baseline=ratio_min, fill=True, alpha=0.15, color=color)
        all_ratios.append(ratio_nom)
        ## MC error
        #plt.errorbar(var_center, ratio_nom, yerr=ratio_err, fmt='none', capsize=0.5, color=color)

    all_ratios = np.concatenate(all_ratios)
    ymin, ymax = np.min(all_ratios), np.max(all_ratios)
    center = 1.0
    pad = max(0.2, 0.2 * (ymax - ymin))  # at least 20% window
    #pad = max(0.1, 0.1 * (ymax - ymin))
    ax_bottom.set_ylim(center - pad, center + pad)

    ax_bottom.axhline(1.0, color="black", lw=1, ls="--")
    xlab = lat
    if unit != "": xlab += " ["+unit+"]"
    ax_bottom.set_xlabel(xlab)
    ax_bottom.set_ylabel("Ratio to NLO")
    ax_bottom.grid(True, ls=":", alpha=0.5)
    if xlims is None:
        ax_bottom.set_xlim(x_min, x_max)
    else:
        ax_bottom.set_xlim(xlims)

    #fig.suptitle(f"Observable: {obs_name}", fontsize=13)
    #plt.tight_layout(rect=[0, 0, 1, 0.97])
    #plt.tight_layout()
    ### default pad_inches is 0.1
    plt.savefig(outfile, bbox_inches='tight', pad_inches=0.05)
    #pdf.savefig()
    plt.close(fig)
    #print(f"Saved: {outfile}")


yscale = ["linear","log","log","log","log"]
latexs = [r"$|y_{j1}|$",r"$p_{t,j1}$",r"$p_{t,j1}$",r"$p_{t,Z}$",r"$p_{t,Z}$"]
units = ["", "GeV","GeV","GeV","GeV"]

observables = ["abs_yj1","ptj1","ptj1_exc","ptz","ptz_y1"]
#observables = ["abs_yj1","ptj1","ptj1_exc","ptz","ptz_y1","abs_yj1_rebin","ptj1_rebin"]

#nreb = [4,2,2,1,1]
nreb = [4,2,2,1,1]
#xlims = [None, (30,450), (30,450), None, None]
xlims = [None, None, None, None, None]

in_dir="results"
out_dir="plots"
Path(out_dir).mkdir(exist_ok=True)
#with PdfPages('plots_exZJ.pdf') as pdf:
for obs,ys,lat,unit,nrb,xlim in zip(observables,yscale,latexs,units,nreb,xlims):
    outfile = Path(out_dir) / f"plot_{obs}.pdf"
    plot_observable(obs, ys, lat, unit, outfile, in_dir, nreb=nrb, xlims=xlim)
