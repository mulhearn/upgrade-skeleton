import FWCore.ParameterSet.Config as cms
import os

# Get command line options
from FWCore.ParameterSet.VarParsing import VarParsing
options = VarParsing ('analysis')

# Set useful defaults
#options.outputFile = "fastcal.root"

options.register(
    'isMC',
    0,
    VarParsing.multiplicity.singleton,
    VarParsing.varType.int,
    'Set to 1 for simulated samples - updates GT, emulates HCAL TPGs.')

options.parseArguments()

process = cms.Process("LegacyEmulation")

process.load('Configuration.StandardSequences.Services_cff')
process.load('Configuration/StandardSequences/FrontierConditions_GlobalTag_cff')
process.load('JetMETCorrections.Configuration.DefaultJEC_cff')
process.load('Configuration/StandardSequences/FrontierConditions_GlobalTag_cff')
process.load('L1Trigger/L1TCalorimeter/legacy_emulation_cfi')

# Load the correct global tag, based on the release
if 'CMSSW_6' in os.environ['CMSSW_VERSION']:
    process.GlobalTag.globaltag = 'POSTLS161_V12::All'
    print "Using global tag for upgrade MC: %s" % process.GlobalTag.globaltag
    if not options.isMC:
        raise ValueError("There is no data in CMSSW 6, you must mean isMC=1")
else:
    if not options.isMC:
        # CMSSW 5 data
        process.GlobalTag.globaltag = 'GR_R_53_V21::All'
    else:
        # CMSSW 5 MC
        process.GlobalTag.globaltag = 'START53_V7B::All'
    process.GlobalTag.connect   = 'frontier://FrontierProd/CMS_COND_31X_GLOBALTAG'
    process.GlobalTag.pfnPrefix = cms.untracked.string('frontier://FrontierProd/')
    print "Using global tag for 52X data: %s" % process.GlobalTag.globaltag

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(options.maxEvents)
)

process.TFileService = cms.Service(
    "TFileService",
    fileName = cms.string(options.outputFile)
)

process.source = cms.Source(
    "PoolSource",
    fileNames = cms.untracked.vstring(options.inputFiles),
    secondaryFileNames = cms.untracked.vstring(options.secondaryInputFiles)
)

# Read inst. lumi. info from the scalers
process.load("EventFilter.ScalersRawToDigi.ScalersRawToDigi_cfi")
process.scalersRawToDigi.scalersInputTag = 'rawDataCollector'

process.dump = cms.EDAnalyzer("EventContentAnalyzer")

process.p1 = cms.Path(
    process.recoObjects *
    process.digiStep*
    process.emulatorStep*
    process.scalersRawToDigi *    
    process.dump
    )

process.schedule = cms.Schedule(
    process.p1
)

# Make the framework shut up.
process.load("FWCore.MessageLogger.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = 100

# Spit out filter efficiency at the end.
process.options = cms.untracked.PSet(wantSummary = cms.untracked.bool(True))
