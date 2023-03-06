#!/bin/bash 
#echo "Defining exposure parameters..." 
# -t -> exposure time, in ms
# -h -> name of target, as it will appear in Fits header
# -n -> number of exposures at this exposure_time 
# -s -> should shutter act normally, opening during exposure (0), or stay closed at all times (1) 
# -g -> Define the gain.  It can be set to 0, 1, or 2, which correspond to low, medium, or high 
#           numbers of ADUs per electron, respectively.  
#           For the PIXIS 1024R, low = (4e-/ADU), medium =(2e-/ADU), and high = (1e-/ADU).
# -r -> the readout speed.  Can be faster and noiser (1) or slower and less noisy (0).
# -p -> specific prefix with which these images will be saved; generally set to object name 
# -f -> focus position of lens, in mm.  Can be between 0 and 28. 
# -u -> universal prefix with which these images will be saved; generally should be observation date 
# -l -> should computer wait to acquire until temperature is locked (1 for yes, 0 for no).  Usually 0. 
# -d -> full path to directory where observations should be saved 
while getopts ":e:o:t:n:s:g:r:p:f:u:l:d:" opt; do
    case $opt in
        e)
             #echo "Setting exposure time to: $OPTARG" >&2
             exp_time=${OPTARG%.*} #We must round exposure time to nearest millisecond 
             echo "Set exposure time (in ms) to: $exp_time"
             ;;
        o)
             echo "Setting target name to: $OPTARG" >&2 
             target_name=$OPTARG
             ;;
        t) 
             echo "Setting end time to: $OPTARG" >&2
             stoptime=$OPTARG
             ;;
        n)
             echo "Setting number of exposures to: $OPTARG"  
             n_exps=$OPTARG
             ;;
        s)
             echo "Setting shutter key to: $OPTARG" >&2
             shutter=$OPTARG
             ;;
        g)
             echo "Setting gain key to: $OPTARG" >&2
             gain_key=$OPTARG
             ;;
        r)
             echo "Setting readout speed key to: $OPTARG" >&2
             fast=$OPTARG
             ;;
        p)
             echo "Setting specific prefix to: $OPTARG" >&2
             specific_prefix=$OPTARG
             ;;
        f)  
             focus_pos=$OPTARG
             echo OPTARG is $OPTARG 
             #echo "Setting focus position to: OPTARG" >&2
             #focus_pos=$OPTARG
             echo focus_pos is now $focus_pos
             ;;
        u)
             echo "Setting universal prefix to: $OPTARG"
             universal_prefix=$OPTARG
             ;;
        l)
             echo "Setting lock key to: $OPTARG" >&2
             do_lock=$OPTARG
             ;;
        d)
             #echo "Setting save directory to: $OPTARG" >&2
             #full_save_dir=$OPTARG
             date_str=$OPTARG
             echo "Setting reference date to $date_str" 
             ;;
        \?)
             echo "Invalid option: -$OPTARG" >&2
             exit 1
             ;;
        :)
             echo "Option -$OPTARG requires an argument." >&2
             exit 1
    esac
done
if [ -z $exp_time ]; then
    exp_time=0.0
fi
if [ -z $stoptime ]; then
    stoptime=2100:01:01:01:01
fi 

if [ -z $target_name ]; then
   target_name="UnknownTarget"
fi  
if [ -z $n_exps ]; then
    n_exps=1
fi
if [ -z $shutter ]; then
    shutter=0
fi
if [ -z $gain_key ]; then
    gain_key=1
fi
if [ -z $fast ]; then
    fast=0 
fi
if [ -z $specific_prefix ]; then
    specific_prefix="MissingName"
fi
if [ -z $date_str ]; then 
    date_str="2000_01_01"
fi
if [ -z $universal_prefix ]; then
    universal_prefix=$date_str"_"
fi
if [ -z $do_lock ]; then
    do_lock=0
fi
if [ -z $focus_pos ]; then
    focus_pos=18.7 #0 is minimium (home); ~25 is maximum of stage given current configuration.  This should be checked whenever spectrograph is redeployed; 28 is maximum of stage itself; 
fi  
if [ -z ${full_save_dir+x} ]; then
#    full_save_dir="/home/sashab/Documents/PIXISData/$date_str/"
     full_save_dir="/home/labuser/Code/Spectrograph/mlof/bin/"
fi 
#Declare exposure time, in ms
#exp_time=400000.0 #600000.0
#Put name of target, as it will appear in Fits header 
#target_name="monochrometer_1100nm" #bias, dark, VLM-635-11 laser, KR-1 spectrum, sky, monochrometer_500nm, ... 
#Declare number of exposures
#n_exps=1
#Define if shutter should act normally, opening during exposure (0), or stay closed at all times (1) 
#shutter=0
#Define the gain.  It can be set to 0, 1, or 2, which correspond to low, medium, or high 
#  numbers of ADUs per electron, respectively.  
# For the PIXIS 1024R, low = (4e-/ADU), medium =(2e-/ADU), and high = (1e-/ADU). 
#gain_key=2
#Define the readout speed.  Can be faster and noiser (1) or slower and less noisy (0). 
#fast=0
#Declare prefix with which images will be saved 
#specific_prefix="mono_1100nm" #should be set to target name
#universal_prefix="_2019_03_21_" #should be set to start date
image_file_prefix=$specific_prefix"_"$universal_prefix
#The name of the temporary file used to store the temperature of the CCD 
parameter_file_prefix="exposure_params" 
#Decide if you want to wait to acquire until temperature is locked 
#do_lock=0

script_dir="/opt/PrincetonInstruments/picam/samples/projects/gcc/objlin/x86_64/debug"
#python_dir="/home/sashab/Documents/sashas_python_scripts/pixis"
python_dir="/home/labuser/Code/Spectrograph/mlof/bin"

#Move stage to specified focus position
#start_stage_home=0
#echo focus_pos is $focus_pos
#echo start_stage_home is $start_stage_home 
#python "$python_dir"/moveStageToFocusPosition.py $focus_pos $start_stage_home  

#full_save_dir="/home/sashab/Documents/PIXISData/2019_03_21/"
if [ ! -d "$full_save_dir" ]; then
  mkdir $full_save_dir 
  chmod -R a+rwX $full_save_dir 
fi

image_number_tracker_file="image_tally.txt"
start_index=1
if [ ! -f $full_save_dir$image_number_tracker_file ]; then
    touch $full_save_dir$image_number_tracker_file  
    echo $start_index-1 > $full_save_dir$image_number_tracker_file
fi 
typeset -i tally=$(cat $full_save_dir$image_number_tracker_file)

remove_raw=1
#for ((i=1;i<=n_exps;i++))
currenttime=$(date +%Y:%m:%d:%H:%M)
sequence_number=1
while [[ "$currenttime" < "$stoptime" ]] && [ "$sequence_number" -le "$n_exps" ]
do
    #currenttime=$(date +%Y:%m:%d:%H:%M)
    echo Current time is "$currenttime" 
    echo Stop time is "$stoptime"
    echo We have not passed stop time. 
    #if [[ "$currenttime" > "$stoptime" ]]
    #then 
    #    echo We have passed stop time. 
    #else 
    #    echo We have not passed stop time. 
    #fi 
    echo Working on exposure "$sequence_number" of "$n_exps ..."
    sequence_number=$(($sequence_number+1))
    tally=$(($tally+1))
    echo "tally is $tally" 

    full_image_file_prefix="$image_file_prefix"
    full_parameter_file_prefix="$parameter_file_prefix"
    full_image_file_prefix="$full_image_file_prefix$tally"
    full_parameter_file_prefix="$full_parameter_file_prefix$tally"
    full_parameter_file_name="$full_parameter_file_prefix.txt" 
    raw_file="$full_image_file_prefix.raw"
    #raw_file="Bias_2021_12_11_1.raw"
    #image_file_name="$full_file_prefix"

    local_start_time=$(date +%Y:%m:%d:%H:%M)
    echo "Acquiring the data using PIXIS commands..."
    if [ "$do_lock" -eq 1 ]; then
        $script_dir/configure_sasha $exp_time 1 $shutter $gain_key $fast $full_image_file_prefix $full_parameter_file_prefix lock
    else
        $script_dir/configure_sasha $exp_time 1 $shutter $gain_key $fast $full_image_file_prefix $full_parameter_file_prefix
    fi
    echo "Raw data acquired.  Now converting to .fits image(s)... "

    echo "Raw data file: $raw_file"

    local_end_time=$(date +%Y:%m:%d:%H:%M)
    python $python_dir/ConvertPIXISRawToFits.py $raw_file $full_image_file_prefix $full_parameter_file_name  "" $full_save_dir "$target_name" $exp_time $shutter $gain_key $fast $focus_pos $local_start_time $local_end_time 
    echo "$raw_file $full_image_file_prefix $full_parameter_file_name  "" $full_save_dir "$target_name" $exp_time $shutter $gain_key $fast $focus_pos $local_start_time $local_end_time"
    echo "Just saved new fits image to $full_save_dir$full_image_file_prefix.fits "
    rm $full_parameter_file_name 
    #optionally, remove the raw data file names
    if [ "$remove_raw" -eq 1 ]; then
        rm $raw_file 
    fi
 
    echo $tally > $full_save_dir$image_number_tracker_file
    currenttime=$(date +%Y:%m:%d:%H:%M) 
done
echo We have either passed the stop time or exceeded the specified number of images to take. Stopping sequence. 

echo "Done."

