//////////////////////////////////////////////////////////////////////////////////
// Configure Sample
// - demonstrates camera setup including:
//   - changing common camera parameters
//   - reading temperature directly from hardware
//   - changing exposure time during acquisition
// - uses the first camera found if any or creates a demo camera
////////////////////////////////////////////////////////////////////////////////

#include <cstring> 
#include <stdlib.h> 
#include <string>
#include <iostream>
#include <sstream>
#include <fstream>
#include <iomanip>
#include "stdio.h"
#include "picam.h"
#include <time.h>

using namespace std;

string ConvertFloatToString(double value_as_float, int target_precision) 
{
    std::ostringstream ss;
    ss << fixed << setprecision(target_precision) << value_as_float;
    string value_as_string (ss.str());
    return value_as_string; 
}

// - prints a number to a file
void PrintToFile(double vals_to_print[], string file_name, int target_precisions[])
{   
    ofstream outputFile;
    outputFile.open(file_name.c_str());
    int n_params_to_print = sizeof(target_precisions)/sizeof(target_precisions[0]) + 1;  
    for( int index = 0; index < n_params_to_print; index = index + 1 ) {
        int target_precision = target_precisions[index]; 
        //int target_precision = 0; 
        string val_to_print = ConvertFloatToString(vals_to_print[index], target_precision); 
        outputFile << val_to_print << "\n" ;
    }
    outputFile.close(); 
}  

// - prints any picam enum
void PrintEnumString( PicamEnumeratedType type, piint value )
{
    const pichar* string;
    Picam_GetEnumerationString( type, value, &string );
    std::cout << string;
    Picam_DestroyString( string );
}

// - prints the camera identity
void PrintCameraID( const PicamCameraID& id )
{
    // - print the model
    PrintEnumString( PicamEnumeratedType_Model, id.model );

    // - print the serial number and sensor
    std::cout << " (SN:" << id.serial_number << ")"
              << " ["    << id.sensor_name   << "]" << std::endl;
}

// - prints error code
void PrintError( PicamError error )
{
    if( error == PicamError_None )
        std::cout << "Succeeded" << std::endl;
    else
    {
        std::cout << "Failed (";
        PrintEnumString( PicamEnumeratedType_Error, error );
        std::cout << ")" << std::endl;
    }
}

// - calculates and prints mean intensity
void CalculateMean( PicamHandle camera, const PicamAvailableData& available )
{
    PicamPixelFormat format;
    Picam_GetParameterIntegerValue(
        camera,
        PicamParameter_PixelFormat,
        reinterpret_cast<piint*>( &format ) );

    piint bit_depth;
    Picam_GetParameterIntegerValue(
        camera,
        PicamParameter_PixelBitDepth,
        &bit_depth );

    if( format == PicamPixelFormat_Monochrome16Bit && bit_depth == 16 )
    {
        piint readout_stride;
        Picam_GetParameterIntegerValue(
            camera,
            PicamParameter_ReadoutStride,
            &readout_stride );

        piint frame_size;
        Picam_GetParameterIntegerValue(
            camera,
            PicamParameter_FrameSize,
            &frame_size );

        const piint pixel_count = frame_size / sizeof( pi16u );
        //std::cout << "available.readout_count: " << std::endl; 
        //std::cout << "available.readout_count: " << available.readout_count << std::endl; 
        for( piint r = 0; r < available.readout_count; ++r )
        {
            const pi16u* pixel = reinterpret_cast<const pi16u*>(
                static_cast<const pibyte*>( available.initial_readout ) +
                r*readout_stride );

            piflt mean = 0.0;
            for( piint p = 0; p < pixel_count; ++p )
                mean += *pixel++;
            mean /= pixel_count;
            // std::cout << "available.readout_count: " << available.readout_count << std::endl; 
            std::cout << "    Mean Intensity: " << mean << std::endl;
        }
    }
}

// - changes some common camera parameters and applies them to hardware
void Configure( PicamHandle camera, float exp_time, int gain_setting, int fast, int shutter)
{
    PicamError error;

    if (gain_setting == 0) {
        // - set low gain
        std::cout << "Set low analog gain ... ";
        error =
            Picam_SetParameterIntegerValue(
                camera,
                PicamParameter_AdcAnalogGain,
                PicamAdcAnalogGain_Low );
        PrintError( error );
    } else if (gain_setting == 1) {
        // - set medium gain
        std::cout << "Set medium analog gain ... ";
        error =
            Picam_SetParameterIntegerValue(
                camera,
                PicamParameter_AdcAnalogGain,
                PicamAdcAnalogGain_Medium );
        PrintError( error );
    } else {
        // - set high gain
        std::cout << "Set high analog gain ... ";
        error = 
            Picam_SetParameterIntegerValue(
                camera,
                PicamParameter_AdcAnalogGain,
                PicamAdcAnalogGain_High );
        PrintError( error );
    }
    
    const PicamCollectionConstraint  *constraint;
    piflt adcSpeed = 0.;

    //Query ADC Speed capabilities
    std::cout << "Acquiring camera collection constraints ... " ; 
    error = 
        Picam_GetParameterCollectionConstraint( 
            camera, 
            PicamParameter_AdcSpeed, 
            PicamConstraintCategory_Capable,
            &constraint ) ; 
    PrintError( error );
    adcSpeed = constraint->values_array[0];
    //Choose slowest speed
    for( piint i = 1; i < constraint->values_count; i++ )
    {   
        if( constraint->values_array[i] < constraint->values_array[i-1] && fast == 0) {
            adcSpeed = constraint->values_array[i];
        }  else {
            adcSpeed = constraint->values_array[i-1]; 
        }
    }

    //TEMPORARY TESTING CODE
    //const PicamCollectionConstraint  *constraint;
    //piflt temp_setPoint = 0.;
    std::cout<<"Acquring temperature set point constraint ... "; 
    error =
        Picam_GetParameterCollectionConstraint(
            camera,
            PicamParameter_SensorTemperatureSetPoint,
            PicamConstraintCategory_Capable,
            &constraint ) ;
    PrintError( error );

    //END TESTING CODE
    Picam_DestroyCollectionConstraints(constraint);

    if (fast == 0) {
        std::cout << "Setting Adc Speed to slow, less noisy readout speed of " << adcSpeed << " MHz ... ";
    } else {
        std::cout << "Setting Adc Speed to fast, noisier readout speed of " << adcSpeed << " MHz ... ";
    } 
    //Set ADC Speed
    error = 
        Picam_SetParameterFloatingPointValue( 
            camera, 
            PicamParameter_AdcSpeed, 
            adcSpeed ); 
    PrintError( error ); 

// - set the shutter to open normally (0) or to stay closed (1)
    if (shutter == 1) {
        // - set shutter to remain closed during exposures 
        std::cout << "Setting shutter to stay closed during exposures ... ";
        error = 
            Picam_SetParameterIntegerValue(
                camera,
                PicamParameter_ShutterTimingMode, 
                PicamShutterTimingMode_AlwaysClosed );
    } else {
        // - set low noise readout
        std::cout << "Setting shutter to act normally, opening during exposures ... ";
        error =
            Picam_SetParameterIntegerValue(
                camera,
                PicamParameter_ShutterTimingMode,
                PicamShutterTimingMode_Normal );
    }
    PrintError( error );


    // - set exposure time (in millseconds) 
    std::cout << "Set " << exp_time << " ms exposure time ... ";  
    error =
        Picam_SetParameterFloatingPointValue(
            camera,
            PicamParameter_ExposureTime,
            exp_time );
    PrintError( error );

    // - show that the modified parameters need to be applied to hardware
    pibln committed;
    Picam_AreParametersCommitted( camera, &committed );
    if( committed )
        std::cout << "Parameters have not changed" << std::endl;
    else
        std::cout << "Parameters have been modified" << std::endl;

    // - apply the changes to hardware
    std::cout << "Commit to hardware: ";
    const PicamParameter* failed_parameters;
    piint failed_parameters_count;
    error =
        Picam_CommitParameters(
            camera,
            &failed_parameters,
            &failed_parameters_count );
    PrintError( error );

    // - print any invalid parameters
    if( failed_parameters_count > 0 )
    {
        std::cout << "The following parameters are invalid:" << std::endl;
        for( piint i = 0; i < failed_parameters_count; ++i )
        {
            std::cout << "    ";
            PrintEnumString(
                PicamEnumeratedType_Parameter,
                failed_parameters[i] );
            std::cout << std::endl;
        }
    }

    // - free picam-allocated resources
    Picam_DestroyParameters( failed_parameters );
}

// - acquires some data and displays the mean intensity
void Acquire( PicamHandle camera )
{
    std::cout << "Acquire data: ";

    // - acquire some data
    const pi64s readout_count = 1;
    const piint readout_time_out = -1;  // infinite
    PicamAvailableData available;
    PicamAcquisitionErrorsMask errors;
    PicamError error =
        Picam_Acquire(
            camera,
            readout_count,
            readout_time_out,
            &available,
            &errors );
    PrintError( error );

    // - print results
    if( error == PicamError_None && errors == PicamAcquisitionErrorsMask_None ) {
       //  std::cout << 'available.readout_count: ' << available.readout_count << std::endl; 
        CalculateMean( camera, available );
    } else
    {
        if( error != PicamError_None )
        {
            std::cout << "    Acquisition failed (";
            PrintEnumString( PicamEnumeratedType_Error, error );
            std::cout << ")" << std::endl;
        }

        if( errors != PicamAcquisitionErrorsMask_None )
        {
            std::cout << "    The following acquisition errors occurred: ";
            PrintEnumString(
                PicamEnumeratedType_AcquisitionErrorsMask,
                errors );
            std::cout << std::endl;
        }
    }
}

// - reads the temperature and temperature status directly from hardware
//   and waits for temperature to lock if requested
void ReadTemperature( PicamHandle camera, pibool lock, piflt* temperature )
{
    PicamError error;

    // - read temperature
    std::cout << "Read sensor temperature: ";
    error =
        Picam_ReadParameterFloatingPointValue(
            camera,
            PicamParameter_SensorTemperatureReading,
            temperature );
    PrintError( error );
    if( error == PicamError_None )
    {
        std::cout << "    " << "Temperature is "
                  << *temperature << " degrees C" << std::endl;
    }

    // - read allowable temperature set point range
    // std::cout << "Getting the allowable Temperature set point range: "
    // set_point_constraint = PicamEMCalibration_GetSensorTemperatureSetPointConstraint(camera);
    // std::cout <<"Temperature constraint is " << *set_point_constraint << std::endl ;  

    // - read temperature status
    std::cout << "Read sensor temperature status: ";
    PicamSensorTemperatureStatus status;
    error =
        Picam_ReadParameterIntegerValue(
            camera,
            PicamParameter_SensorTemperatureStatus,
            reinterpret_cast<piint*>( &status ) );
    PrintError( error );
    if( error == PicamError_None )
    {
        std::cout << "    " << "Status is ";
        PrintEnumString( PicamEnumeratedType_SensorTemperatureStatus, status );
        std::cout << std::endl;
    }

    // - read temperature set point 


    // - wait indefinitely for temperature to lock if requested
    if( lock )
    {
        std::cout << "Waiting for temperature lock: ";
        error =
            Picam_WaitForStatusParameterValue(
                camera,
                PicamParameter_SensorTemperatureStatus,
                PicamSensorTemperatureStatus_Locked,
                -1 );
        PrintError( error );
    }
}


// - Saves a single frames worth of data to a raw filter 
void SaveData( PicamHandle camera, const PicamAvailableData& available, string file_name)
{  
    FILE *pFile;  
    // std::cout << "We have defined SaveData" << std::endl; 
    piint bit_depth;
    Picam_GetParameterIntegerValue(
        camera,
        PicamParameter_PixelBitDepth,
        &bit_depth );
    // std::cout << "bit_depth: " << bit_depth << std::endl; 

    piint readoutstride = 0;
    Picam_GetParameterIntegerValue( 
        camera, 
        PicamParameter_ReadoutStride, 
        &readoutstride );
    // std::cout << "readoutstride: " << readoutstride << std::endl; 

    // std::cout << "available.readout_count: " << available.readout_count << std::endl;
    // std::cout << "available.initial_readout:" << std::endl;
    // std::cout << available.initial_readout << std::endl;
    pFile = fopen( file_name.c_str(), "wb" );
    if( pFile )
    {
        if( !fwrite( available.initial_readout, 1, (available.readout_count * readoutstride), pFile ) ) 
        {
             std::cout << "Data file not saved" << std::endl;
        } else {
             //std::cout << "Data file saved" << std::endl;
        }
        
        //std::cout << "pFile seemingly defined." << std::endl; 
        fclose( pFile );
    }

}

// - acquires data while changing exposure time
void AcquireAndExposeAndSave( PicamHandle camera, int readout_count, string image_file_prefix, string parameter_file_prefix )
{
    PicamError error;

    // - set to acquire 10 readouts
    std::cout << "Set " << readout_count << " readouts: ";
    // const pi64s readout_count = 10;
    error =
        Picam_SetParameterLargeIntegerValue(
            camera,
            PicamParameter_ReadoutCount,
            readout_count );
    PrintError( error );

    // - commit
    std::cout << "Commit to hardware: ";
    const PicamParameter* failed_parameters;
    piint failed_parameters_count;
    error =
        Picam_CommitParameters(
            camera,
            &failed_parameters,
            &failed_parameters_count );
    Picam_DestroyParameters( failed_parameters );
    PrintError( error );

    // - acquire asynchronously
    std::cout << "Acquire:" << std::endl;
    std::cout << "    Start: ";
    error = Picam_StartAcquisition( camera );
    PrintError( error );

    // - acquisition loop
    const piint readout_time_out = -1;  // infinite
    PicamAvailableData available;
    PicamAcquisitionStatus status;
    pibool running = true;
    pi64s readouts_acquired = 0;
    // pibool changed_exposure = true;
    time_t start_time; 
    time_t end_time; 
    time(&start_time); 
    while( (error == PicamError_None || error == PicamError_TimeOutOccurred) &&
           running )
    {
        // - wait for data, completion or failure
        error =
            Picam_WaitForAcquisitionUpdate(
                camera,
                readout_time_out,
                &available,
                &status );

        // - display each result
        if( error == PicamError_None &&
            status.errors == PicamAcquisitionErrorsMask_None )
        {
            running = status.running != 0;
            readouts_acquired += available.readout_count;
            time(&end_time); 
            //cout << "start_time = " << start_time << " and end_time = " << end_time << std::endl; 
            if( available.readout_count ) 
            { // - read temperature
                // std::cout << "Read sensor temperature: ";
                piflt temperature;
                error = Picam_ReadParameterFloatingPointValue(
                                                              camera,
                                                              PicamParameter_SensorTemperatureReading,
                                                              &temperature );
                // PrintError( error );
                if( error == PicamError_None )
                {
                    std::cout << "" << "Temperature is "
                              << temperature << " degrees C" << std::endl;
                } else {
                    std::cout << "" << "Temperature reading failed on this observation!" << std::endl; 
                }

                CalculateMean( camera, available );
                std::stringstream image_name_stream;
                std::stringstream parameter_name_stream; 
	        image_name_stream << image_file_prefix << ".raw"; 
                parameter_name_stream << parameter_file_prefix << ".txt";
                string new_image_name = image_name_stream.str(); 
                string new_parameter_name = parameter_name_stream.str(); 
                std::cout << "Saving readout to file: " << new_image_name << std::endl; 
                SaveData( camera, available, new_image_name );
                double start_float = start_time; 
                double end_float = end_time; 
                double temperature_float = temperature; 
                double array_to_print [] = {temperature_float, start_float, end_float};
                int precision_of_params_to_print [] = {0, 0, 0}; 
                PrintToFile(array_to_print, new_parameter_name, precision_of_params_to_print );    
            } 
        }
        else
        {
            if( error != PicamError_None )
            {
                std::cout << "    Acquisition failed (";
                PrintEnumString( PicamEnumeratedType_Error, error );
                std::cout << ")" << std::endl;
            }

            if( status.errors != PicamAcquisitionErrorsMask_None )
            {
                std::cout << "    The following acquisition errors occurred: ";
                PrintEnumString(
                    PicamEnumeratedType_AcquisitionErrorsMask,
                    status.errors );
                std::cout << std::endl;
            }
        }
    }
}

int main( int argc, char* argv[] )
{ 
    // - set formatting options
    std::cout << std::boolalpha;

    // - user must specify exp_time, n_frames, and 
    float default_exp_time = 50.0;
    int default_readout_count = 1;
    int default_gain_setting = 2; 
    int default_fast = 0;
    int default_shutter = 0; 
    string default_image_file_prefix = "my_sample";
    string default_parameter_file_prefix = "exposure_params"; 
    float exp_time; 
    int readout_count;
    int gain_setting;  
    int fast; 
    int shutter; 
    string image_file_prefix; 
    string parameter_file_prefix; 
    shutter = default_shutter;
    if (argc < 2)
    {    std::cout << "User did not provide exposure time.  Will use default value of " << default_exp_time << "ms. " << std::endl;
         exp_time = default_exp_time; 
    }
    else {
         exp_time = atof(argv[1]);
    }
    if (argc < 3)
    {    std::cout << "User did not provide number of exposures.  Will use default value of " << default_readout_count << std::endl;
         readout_count = default_readout_count; 
    }
    else {
         readout_count = atoi(argv[2]);
    }
    if (argc < 4)
    {    std::cout << "User did not indicate if shutter should act normally or be fixed closed.  Will use default value of " << default_shutter << std::endl;
         shutter = default_shutter;
    }
    else {
         shutter = atoi(argv[3]);
    }
    if (argc < 5)
    {    std::cout << "User did not provide gain setting.  Will use default value of " << default_gain_setting << std::endl;
         gain_setting = default_gain_setting; 
    }
    else {
         gain_setting = atoi(argv[4]);
    }
    if (argc < 6)
    {    std::cout << "User did not indicate if readout should be fast.  Will use default value of " << default_fast << std::endl;
         fast = default_fast; 
    }
    else {
         fast = atoi(argv[5]);
    }
    if (argc < 7)
    {    std::cout << "User did not give root of image file name.  Will use default value of " << default_image_file_prefix << std::endl;
         image_file_prefix = default_image_file_prefix;
    }
    else {
         image_file_prefix = argv[6];
    }
    if (argc < 8)
    {    std::cout << "User did not give name of exposure parameter file.  Will use default value of " << default_parameter_file_prefix  << std::endl;
         parameter_file_prefix = default_parameter_file_prefix ;
    }
    else {
         parameter_file_prefix = argv[7];
    }

    std::cout << "Exposure time is "<< exp_time << "ms.  "<< std::endl;
    std::cout << "Number of exposures (i.e. readout_count) is "<< readout_count << std::endl; 
    std::cout << "Shutter setting is "<< shutter << ". The shutter key is: {0 : shutter open and only open during exposures, 1 : shutter always closed}" << std::endl;
    std::cout << "Gain setting is " << gain_setting <<".  The gain key is: {0 : 4e-/ADU, 1 : 2e-/ADU, 2 : 1e-/ADU} " << std::endl ;
    std::cout << "Readout setting is " << fast << ". The readout key is: {1 : 2Mhz, ~9e- rms, 0 : 0.1Mhz, ~3e- rms}. " << std::endl; 
    std::cout << "Prefix for saved data is " << image_file_prefix << std::endl; 
    std::cout << "Prefix for saved parameter values is " << parameter_file_prefix << std::endl; 

    // - allow the optional argument 'lock' to wait for temperature lock
    pibool lock = false;
    if( argc == 9 )
    {
        std::string arg( argv[8] );
        if( arg == "lock" )
            lock = true;
        else
        {
            std::cout << "Invalid argument to lock temperature.";
            return -1;
        }
    }

    Picam_InitializeLibrary();

    // - open the first camera if any or create a demo camera
    PicamHandle camera;
    PicamCameraID id;
    if( Picam_OpenFirstCamera( &camera ) == PicamError_None )
        Picam_GetCameraID( camera, &id );
    else
    {
        Picam_ConnectDemoCamera(
            PicamModel_Pixis100B,
            "12345",
            &id );
        Picam_OpenCamera( &id, &camera );
    }

    PrintCameraID( id );
    std::cout << std::endl;

    std::cout << "Configuration" << std::endl
              << "=============" << std::endl;
    Configure( camera, exp_time, gain_setting, fast, shutter );
    //Acquire( camera );
    std::cout << std::endl;

    std::cout << "Temperature" << std::endl
              << "===========" << std::endl;
    //piflt* temperature_pointer;
    double temperature = 1000.0;  
    //#temperature_pointer = &temperature; 
    //#*temperature_pointer = 1000.0; 
    ReadTemperature( camera, lock, &temperature );
    std::cout << std::endl; 

    //Print the temperature to a file 
    std::ostringstream ss; 
    ss << temperature;
    string temp_string(ss.str());
    string default_parameter_file_name; 
    default_parameter_file_name.append(default_parameter_file_prefix); 
    default_parameter_file_name.append(".txt");   
    //PrintToFile(temp_string, default_parameter_file_prefix);

    //int readout_count = 8; 
    std::cout << "Starting Series of Exposures" << std::endl
              << "===============" << std::endl;
    for (int i=1; i<=readout_count; i++) {
        string new_image_file_prefix; 
        new_image_file_prefix.append(image_file_prefix); 
        //new_image_file_prefix.append(ConvertFloatToString(static_cast< float > (i), 0));
        string new_parameter_file_prefix; 
        new_parameter_file_prefix.append(parameter_file_prefix); 
        //new_parameter_file_prefix.append(ConvertFloatToString(static_cast< float > (i), 0));

        AcquireAndExposeAndSave( camera, 1, new_image_file_prefix, new_parameter_file_prefix );
        std::cout << std::endl;
    } 

    Picam_CloseCamera( camera );

    Picam_UninitializeLibrary();
}
