import numpy as np
from glob import glob

def read_input(inputfile):
    import h5py
    import os
    list_input = open("%s"%inputfile)
    nfiles=0
    for line in list_input:
        fname = line.rstrip()
        if fname.startswith('#'):
            continue
        if not os.path.getsize(fname):
            continue
        print("read file", fname)
        h5f = h5py.File( fname, 'r')
        if nfiles == 0:
           X = h5f['X'][:]
           Y = h5f['Y'][:]
    
        else:
           X = np.concatenate((X, h5f['X']), axis=0)
           Y = np.concatenate((Y, h5f['Y']), axis=0)
        h5f.close()
        nfiles += 1
    
    print("finish reading files")
    A = X[:, :, :]
    B = Y[:, :]
    return A, B

def convertXY2PtPhi(arrayXY):
    # convert from array with [:,0] as X and [:,1] as Y to [:,0] as pt and [:,1] as phi
    nevents = arrayXY.shape[0]
    arrayPtPhi = np.zeros((nevents, 2))
    arrayPtPhi[:,0] = np.sqrt((arrayXY[:,0]**2 + arrayXY[:,1]**2))
    arrayPtPhi[:,1] = np.sign(arrayXY[:,1])*np.arccos(arrayXY[:,0]/arrayPtPhi[:,0])
    return arrayPtPhi

def preProcessing(X, EVT=None):
    """ pre-processing input """
    A = X[:, :, :]

    norm = 50.0

    pt = A[:,:,0:1] / norm
    px = A[:,:,1:2] / norm
    py = A[:,:,2:3] / norm
    eta = A[:,:,3:4]
    phi = A[:,:,4:5]
    puppi = A[:,:,5:6]

    # remove outliers
    pt[ np.where(np.abs(pt>500)) ] = 0.
    px[ np.where(np.abs(px>500)) ] = 0.
    py[ np.where(np.abs(py>500)) ] = 0.

    inputs = np.concatenate((pt, eta, phi, puppi, px, py), axis=2)

    inputs_cat0 = A[:,:,6:7] # encoded PF pdgId
    inputs_cat1 = A[:,:,7:8] # encoded PF charge

    return inputs, inputs_cat0, inputs_cat1

def MakePlots(truth_XY, predict_XY, PUPPI_XY, path_out):
    # make the 1d distribution, response, resolution, 
    # and response-corrected resolution plots
    # assume the input has [:,0] as X and [:,1] as Y
    import matplotlib.pyplot as plt
    import mplhep as hep
    plt.style.use(hep.style.CMS)
    truth_PtPhi = convertXY2PtPhi(truth_XY)
    predict_PtPhi = convertXY2PtPhi(predict_XY)
    PUPPI_PtPhi = convertXY2PtPhi(PUPPI_XY)
    Make1DHists(truth_XY[:,0], predict_XY[:,0], PUPPI_XY[:,0], -400, 400, 40, False, 'MET X [GeV]', 'A.U.', f'{path_out}MET_x.png')
    Make1DHists(truth_XY[:,1], predict_XY[:,1], PUPPI_XY[:,1], -400, 400, 40, False, 'MET Y [GeV]', 'A.U.', f'{path_out}MET_y.png')
    Make1DHists(truth_PtPhi[:,0], predict_PtPhi[:,0], PUPPI_PtPhi[:,0], 0, 400, 40, False, 'MET Pt [GeV]', 'A.U.', f'{path_out}MET_pt.png')
    # do statistics
    from scipy.stats import binned_statistic
    binnings = np.linspace(0, 400, num=21)
    print(binnings)
    truth_means,    bin_edges, binnumber = binned_statistic(truth_PtPhi[:,0], truth_PtPhi[:,0],    statistic='mean', bins=binnings, range=(0,400))
    predict_means,  _,         _ = binned_statistic(truth_PtPhi[:,0], predict_PtPhi[:,0],  statistic='mean', bins=binnings, range=(0,400))
    PUPPI_means, _,         _ = binned_statistic(truth_PtPhi[:,0], PUPPI_PtPhi[:,0], statistic='mean', bins=binnings, range=(0,400))
    # plot response
    plt.figure()
    plt.hlines(truth_means/truth_means, bin_edges[:-1], bin_edges[1:], colors='k', lw=5,
           label='Truth', linestyles='solid')
    plt.hlines(predict_means/truth_means, bin_edges[:-1], bin_edges[1:], colors='r', lw=5,
           label='Predict', linestyles='solid')
    plt.hlines(PUPPI_means/truth_means, bin_edges[:-1], bin_edges[1:], colors='g', lw=5,
           label='PUPPI', linestyles='solid')
    plt.xlim(0,400.0)
    plt.ylim(0,1.1)
    plt.xlabel('Truth MET [GeV]')
    plt.legend(loc='lower right')
    plt.ylabel('<MET Estimation>/<MET Truth>')
    plt.savefig(f"{path_out}MET_response.png")
    plt.close()
    # response correction factors
    sfs_truth    = np.take(truth_means/truth_means,    np.digitize(truth_PtPhi[:,0], binnings)-1, mode='clip')
    sfs_predict  = np.take(predict_means/truth_means,  np.digitize(truth_PtPhi[:,0], binnings)-1, mode='clip')
    sfs_PUPPI = np.take(PUPPI_means/truth_means, np.digitize(truth_PtPhi[:,0], binnings)-1, mode='clip')
    # resolution defined as (q84-q16)/2.0
    def resolqt(y):
        return(np.percentile(y,84)-np.percentile(y,16))/2.0
    bin_resolX_predict, bin_edges, binnumber = binned_statistic(truth_PtPhi[:,0], truth_XY[:,0] - predict_XY[:,0] * sfs_predict, statistic=resolqt, bins=binnings, range=(0,400))
    bin_resolY_predict, _, _                 = binned_statistic(truth_PtPhi[:,0], truth_XY[:,1] - predict_XY[:,1] * sfs_predict, statistic=resolqt, bins=binnings, range=(0,400))
    bin_resolX_PUPPI, _, _                = binned_statistic(truth_PtPhi[:,0], truth_XY[:,0] - PUPPI_XY[:,0] * sfs_predict, statistic=resolqt, bins=binnings, range=(0,400))
    bin_resolY_PUPPI, _, _                = binned_statistic(truth_PtPhi[:,0], truth_XY[:,1] - PUPPI_XY[:,1] * sfs_predict, statistic=resolqt, bins=binnings, range=(0,400))
    plt.figure()
    plt.hlines(bin_resolX_predict, bin_edges[:-1], bin_edges[1:], colors='r', lw=5,
           label='Predict', linestyles='solid')
    plt.hlines(bin_resolX_PUPPI, bin_edges[:-1], bin_edges[1:], colors='g', lw=5,
           label='PUPPI', linestyles='solid')
    plt.legend(loc='lower right')
    plt.xlim(0,400.0)
    plt.ylim(0,200.0)
    plt.xlabel('Truth MET [GeV]')
    plt.ylabel('RespCorr $\sigma$(METX) [GeV]')
    plt.savefig(f"{path_out}resolution_metx.png")
    plt.close()
    plt.figure()
    plt.hlines(bin_resolY_predict, bin_edges[:-1], bin_edges[1:], colors='r', lw=5,
           label='Predict', linestyles='solid')
    plt.hlines(bin_resolY_PUPPI, bin_edges[:-1], bin_edges[1:], colors='g', lw=5,
           label='PUPPI', linestyles='solid')
    plt.legend(loc='lower right')
    plt.xlim(0,400.0)
    plt.ylim(0,200.0)
    plt.xlabel('Truth MET [GeV]')
    plt.ylabel('RespCorr $\sigma$(METY) [GeV]')
    plt.savefig(f"{path_out}resolution_mety.png")
    plt.close()




def Make1DHists(truth, predict, PUPPI, xmin=0, xmax=400, nbins=100, density=False, xname="pt [GeV]", yname = "A.U.", outputname="1ddistribution.png"):
    import matplotlib.pyplot as plt
    import mplhep as hep
    plt.style.use(hep.style.CMS)
    plt.figure(figsize=(10,8))
    plt.hist(truth,    bins=nbins, range=(xmin, xmax), density=density, histtype='step', facecolor='k', label='Truth')
    plt.hist(predict,  bins=nbins, range=(xmin, xmax), density=density, histtype='step', facecolor='r', label='Predict')
    plt.hist(PUPPI, bins=nbins, range=(xmin, xmax), density=density, histtype='step', facecolor='g', label='PUPPI')
    plt.yscale('log')
    plt.legend(loc='upper right')
    plt.xlabel(xname)
    plt.ylabel(yname)
    plt.savefig(outputname)
    plt.close()