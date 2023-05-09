# -*- coding: utf-8 -*-
include('builtin')

#----------- Snapshots with snapbase ----------------------
FileType('Snapshot', '2D Image', 'AIMS image formats')
FileType('Snapshot Grey White', 'Snapshot', 'PNG image')
FileType('Snapshot Split Brain', 'Snapshot', 'PNG image')
FileType('Snapshot Meshcut', 'Snapshot', 'PNG image')
FileType('Snapshot Pial Mesh', 'Snapshot', 'PNG image')
FileType('Snapshot Sulci', 'Snapshot', 'PNG image')
FileType('Snapshot White Mesh', 'Snapshot', 'PNG image')
FileType('Snapshot Brain Mask', 'Snapshot', 'PNG image')
FileType('Snapshot Raw T1', 'Snapshot', 'PNG image')
FileType('Snapshot Tablet Raw T1', 'Snapshot', 'PNG image')
FileType('Snapshot Probability Map', 'Snapshot', 'PNG image')
FileType('Snapshots Probability Map Quality Scores', 'CSV file', 'CSV file')
FileType('Snapshot Thickness Map', 'Snapshot', 'PNG image')
FileType('Snapshot Gyral Parcellation', 'Snapshot', 'PNG image')
FileType('Snapshot Curvature Map', 'Snapshot', 'PNG image')

FileType('Snapshot SPM Analysis PET Result Map', 'Snapshot', 'PNG image')

FileType('Snapshots Grey White Quality Scores', 'CSV file')
FileType('Snapshots Split Brain Quality Scores', 'CSV file')
FileType('Snapshots Meshcut Quality Scores', 'CSV file')
FileType('Snapshots Pial Mesh Quality Scores', 'CSV file')
FileType('Snapshots Sulci Quality Scores', 'CSV file')
FileType('Snapshots White Mesh Quality Scores', 'CSV file')

FileType('Numerical Table', 'CSV file')
FileType('Sulcal Openings Table', 'Numerical Table')
FileType('Cortical Thicknesses Table', 'Numerical Table')
FileType('Global Volumetry Table', 'Numerical Table')
FileType('Hippocampal Volumetry Table', 'Numerical Table')

FileType('History Sulcal Openings Table', 'Text file')
FileType('History Cortical Thicknesses Table', 'Text file')
FileType('History Global Volumetry Table', 'Text file')
FileType('History Hippocampal Volumetry Table', 'Text file')
FileType('Normative brain volumes stats', 'Any Type', 'JSON file')

FileType('Snapshots Features Table', 'Numerical Table')
