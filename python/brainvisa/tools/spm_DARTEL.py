# -*- coding: utf-8 -*-

#
# Functions used for DARTEL processes (spm8 or spm12)
#


#
# Initialize 'Run DARTEL: create Template' tool with
# default parameters from SPM8 (same in SPM12b)
#
def initialize_DARTEL_create_templates_parameters_withSPM8Default( process ):
    
    process.Template_basename = 'Template'
    process.Regularisation_form = '0'
    # Outer Iteration 1
    process.Inner_iteration_1 = 3
    process.Regularisation_parameters_1 = '[4 2 1e-06]'
    process.Time_step_1 = 0
    process.Smoothing_parameter_1 = 16
    
    # Outer Iteration 2
    process.Inner_iteration_2 = 3
    process.Regularisation_parameters_2 = '[2 1 1e-06]'
    process.Time_step_2 = 0
    process.Smoothing_parameter_2 = 8
    
    # Outer Iteration 3    
    process.Inner_iteration_3 = 3
    process.Regularisation_parameters_3 = '[1 0.5 1e-06]'
    process.Time_step_3 = 1
    process.Smoothing_parameter_3 = 4
    
    # Outer Iteration 4
    process.Inner_iteration_4 = 3
    process.Regularisation_parameters_4 = '[0.5 0.25 1e-06]'
    process.Time_step_4 = 2
    process.Smoothing_parameter_4 = 2
    
    # Outer Iteration 5
    process.Inner_iteration_5 = 3
    process.Regularisation_parameters_5 = '[0.25 0.125 1e-06]'
    process.Time_step_5 = 4
    process.Smoothing_parameter_5 = 1
    
    # Outer Iteration 6
    process.Inner_iteration_6 = 3
    process.Regularisation_parameters_6 = '[0.25 0.125 1e-06]'
    process.Time_step_6 = 6
    process.Smoothing_parameter_6 = 0.5
    
    # Optimisation settings
    process.LM_Regularisation = 0.01
    process.Cycles = 3
    process.Iterations = 3

#----------------------------------------------------------------------------------
# 
# Create DARTEL create Templates batch job (for SPM8 and 12)
#
def write_DARTEL_create_Templates_batch( self, spmJobFile, images_1_path, images_2_path, template_basename, reg_form, inner_iteration, reg_params, time_step, smooth_param, LM_reg, cycles, iterations ):
    mat_file = open(spmJobFile, 'w')
    
    images_1 = """{"""
    for img in images_1_path:
        images_1 += "\n\t'" + img + "'"
    images_1 += """}""" 
    
    images_2 = """"""
    if len( images_2_path ) > 0 and len( images_1_path ) == len( images_2_path ):
        images_2 = """{"""
        for img in images_2_path:
            images_2 += "\n\t'" + img + "'"
        images_2 += """}""" 
    
    mat_file.write("""
        matlabbatch{1}.spm.tools.dartel.warp.images = {
                                               %s
                                               %s
                                               };
        matlabbatch{1}.spm.tools.dartel.warp.settings.template = '%s';
        matlabbatch{1}.spm.tools.dartel.warp.settings.rform = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(1).its = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(1).rparam = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(1).K = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(1).slam = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(2).its = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(2).rparam = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(2).K = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(2).slam = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(3).its = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(3).rparam = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(3).K = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(3).slam = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(4).its = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(4).rparam = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(4).K = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(4).slam = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(5).its = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(5).rparam = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(5).K = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(5).slam = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(6).its = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(6).rparam = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(6).K = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.param(6).slam = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.optim.lmreg = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.optim.cyc = %s;
        matlabbatch{1}.spm.tools.dartel.warp.settings.optim.its = %s;
        """ % ( images_1, images_2, template_basename, reg_form,  
                inner_iteration[0], reg_params[0], time_step[0], smooth_param[0],
                inner_iteration[1], reg_params[1], time_step[1], smooth_param[1],
                inner_iteration[2], reg_params[2], time_step[2], smooth_param[2],
                inner_iteration[3], reg_params[3], time_step[3], smooth_param[3],
                inner_iteration[4], reg_params[4], time_step[4], smooth_param[4],
                inner_iteration[5], reg_params[5], time_step[5], smooth_param[5],
                LM_reg, cycles, iterations
                ) )
    
    mat_file.close()
    
    return mat_file.name

#------------------------------------------------------- 
# Initialize 'DARTEL: create warped' tool with
# default parameters from SPM8 (same in SPM12b)
#
def initialize_DARTEL_create_warped_parameters_withSPM8Default( process ):
    process.Modulation = 'Preserve concentration ("no modulation")'
    process.Time_steps = 64
    process.Interpolation = 'Trilinear'
    

#----------------------------------------------------------------------------------
# 
# Create DARTEL warped images batch job (for SPM8 and 12)
#   
def write_DARTEL_create_warped_batch( self, spmJobFile, flow_fields_path, images_path, modulation, time_steps, interpolation ):
    
    mat_file = open(spmJobFile, 'w')
    
    flow_fields = """{"""
    for img in flow_fields_path:
        flow_fields += "\n\t'" + img + "'"
    flow_fields += """}""" 
    
    images = """{"""
    for img in images_path:
        images += "\n\t'" + img + "'"
    images += """}""" 
    
    mat_file.write("""
            matlabbatch{1}.spm.tools.dartel.crt_warped.flowfields = %s;
            matlabbatch{1}.spm.tools.dartel.crt_warped.images = {
                                                                %s
            };
            matlabbatch{1}.spm.tools.dartel.crt_warped.jactransf = %s;
            matlabbatch{1}.spm.tools.dartel.crt_warped.K = %s;
            matlabbatch{1}.spm.tools.dartel.crt_warped.interp = %s; 
        """% ( flow_fields, images, modulation, time_steps, interpolation ) )

    mat_file.close()
    
    return mat_file.name