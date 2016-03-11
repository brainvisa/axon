# -*- coding: utf-8 -*-
from soma.spm.virtual_spm.stats.results_report import ResultsReport as ResultsReport_virtual
from soma.spm.spm_main_module import SPM12MainModule
from soma.spm.custom_decorator_pattern import checkIfArgumentTypeIsAllowed
from soma.spm.spm_batch_maker_utils import addBatchKeyWordInEachItem

from soma.spm.spm8.stats.results_report.contrast_query_container import ContrastQueryContainer
from soma.spm.spm12.stats.results_report.write_filtered_images import WriteFilteredImages

class ResultsReport(ResultsReport_virtual, SPM12MainModule):
  def __init__(self):
    self.matlab_file_path = None
    self.contrast_query_container = ContrastQueryContainer()
    self.data_type = 1
    self.print_result = 'ps'

  def enablePrintResult(self):
    raise NotImplementedError("it is deprecated in SPM12")

  def disablePrintResult(self):
    raise NotImplementedError("it is deprecated in SPM12")

  def unsetPrintResults(self):
    self.print_result = 'false'

  def setPrintResultsToPS(self):
    self.print_result = "'ps'"

  def setPrintResultsToEPS(self):
    self.print_result = "'eps'"

  def setPrintResultsToPDF(self):
    self.print_result = "'pdf'"

  def setPrintResultsToJPEG(self):
    self.print_result = "'jpg'"

  def setPrintResultsToPNG(self):
    self.print_result = "'png'"

  def setPrintResultsToTIFF(self):
    self.print_result = "'tif'"

  def setPrintResultsToMatlabFigure(self):
    self.print_result = "'fig'"

  def setPrintResultsToCSV(self):
    self.print_result = "'csv'"

  def setPrintResultsToNiDM(self):
    self.print_result = "'nidm'"

  def unsetWriteFilteredImages(self):
    self.write_filtered_images = None

  @checkIfArgumentTypeIsAllowed(WriteFilteredImages, 1)
  def setWriteFilteredImages(self, write_filtered_images):
    self.write_filtered_images = write_filtered_images

  def getStringListForBatch( self ):
    if self.matlab_file_path is not None:
      batch_list = []
      batch_list.append("spm.stats.results.spmmat = {'%s'};" % self.matlab_file_path)
      batch_list.append("spm.stats.results.units = %i;" % self.data_type)
      batch_list.append("spm.stats.results.print = %s;" % self.print_result)
      batch_list.extend(addBatchKeyWordInEachItem("spm.stats.results", self.contrast_query_container.getStringListForBatch()))
      if self.write_filtered_images is not None:
        batch_list.extend(addBatchKeyWordInEachItem("spm.stats.results", self.write_filtered_images.getStringListForBatch()))
      else:
        batch_list.append("spm.stats.results.write.none = 1;")
      return batch_list
    else:
      raise ValueError('Unvalid Model estimation, Mat file not found')
