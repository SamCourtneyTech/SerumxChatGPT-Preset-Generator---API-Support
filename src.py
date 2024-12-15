import openai
from pythonosc import udp_client
import random
import re
import bisect
from pythonosc import dispatcher, osc_server
import json
import time

#openai.api_key =

last_trigger_time = 0
trigger_interval = 5
serum_default_parameters =\
[
["Env1 Atk", "0.5 ms"],
["Env1 Hold", "0.0 ms"],
["Env1 Dec", "1.00 s"],
["Env1 Sus", "0.0 dB"],
["Env1 Rel", "15 ms"],
["Osc A On", "on"],
["A UniDet", "0.25"],
["A UniBlend", "75"],
["A WTPos", "Sine"],
["A Pan", "0"],
["A Vol", "75%"],
["A Unison", "1"],
["A Octave", "0 Oct"],
["A Semi", "0 semitones"],
["A Fine", "0 cents"],
["Fil Type", "MG Low 12"],
["Fil Cutoff", "425 Hz"],
["Fil Reso", "10%"],
["Filter On", "off"],
["Fil Driv", "0%"],
["Fil Var", "0%"],
["Fil Mix", "100%"],
["OscA>Fil", "on"],
["OscB>Fil", "off"],
["OscN>Fil", "off"],
["OscS>Fil", "off"],
["Osc N On", "off"],
["Noise Pitch", "50%"],
["Noise Level", "25%"],
["Osc S On", "off"],
["Sub Osc Level", "75%"],
["SubOscOctave", "0 Oct"],
["SubOscShape", "Sine"],
["Osc B On", "off"],
["B UniDet", "0.25"],
["B UniBlend", "75"],
["B WTPos", "1"],
["B Pan", "0"],
["B Vol", "75%"],
["B Unison", "1"],
["B Octave", "0 Oct"],
["B Semi", "0 semitones"],
["B Fine", "0 cents"],
["Hyp Enable", "off"],
["Hyp_Rate", "40%"],
["Hyp_Detune", "25%"],
["Hyp_Retrig", "off"],
["Hyp_Wet", "50%"],
["Hyp_Unision", "4"],
["HypDim_Size", "50%"],
["HypDim_Mix", "0%"],
["Dist Enable", "off"],
["Dist_Mode", "Tube"],
["Dist_PrePost", "Off"],
["Dist_Freq", "330 Hz"],
["Dist_BW", "1.9"],
["Dist_L/B/H", "0%"],
["Dist_Drv", "25%"],
["Dist_Wet", "100%"],
["Flg Enable", "off"],
["Flg_Rate", "0.08 Hz"],
["Flg_BPM_Sync", "off"],
["Flg_Dep", "100%"],
["Flg_Feed", "50%"],
["Flg_Stereo", "180deg."],
["Flg_Wet", "100%"],
["Phs Enable", "off"],
["Phs_Rate", "0.08 Hz"],
["Phs_BPM_Sync", "off"],
["Phs_Dpth", "50%"],
["Phs_Frq", "600 Hz"],
["Phs_Feed", "80%"],
["Phs_Stereo", "180deg."],
["Phs_Wet", "100%"],
["Cho Enable", "off"],
["Cho_Rate", "0.08 Hz"],
["Cho_BPM_Sync", "off"],
["Cho_Dly", "5.0 ms"],
["Cho_Dly2", "0.0 ms"],
["Cho_Dep", "26.0 ms"],
["Cho_Feed", "10%"],
["Cho_Filt", "1000 Hz"],
["Cho_Wet", "50%"],
["Dly Enable", "off"],
["Dly_Feed", "40%"],
["Dly_BPM_Sync", "on"],
["Dly_Link", "Unlink, Link"],
["Dly_TimL", "1/4"],
["Dly_TimR", "1/4"],
["Dly_BW", "6.8"],
["Dly_Freq", "849 Hz"],
["Dly_Mode", "Normal"],
["Dly_Wet", "30%"],
["Comp Enable", "off"],
["Cmp_Thr", "-18.1 dB"],
["Cmp_Att", "90.1 ms"],
["Cmp_Rel", "90 ms"],
["CmpGain", "0.0 dB"],
["CmpMBnd", "Normal"],
["Comp_Wet", "100"],
["Rev Enable", "off"],
["VerbSize", "35%"],
["Decay", "4.7 s"],
["VerbLoCt", "0%"],
["VerbHiCt", "35%"],
["Spin Rate", "25%"],
["Verb Wet", "20%"],
["EQ Enable", "off"],
["EQ FrqL", "210 Hz"],
["EQ Q L", "60%"],
["EQ VolL", "0.0 dB"],
["EQ TypL", "Shelf"],
["EQ TypeH", "Shelf"],
["EQ FrqH", "2041 Hz"],
["EQ Q H", "60%"],
["EQ VolH", "0.0"],
["FX Fil Enable", "off"],
["FX Fil Type", "MG Low 6"],
["FX Fil Freq", "330 Hz"],
["FX Fil Reso", "0%"],
["FX Fil Drive", "0%"],
["FX Fil Pan", "50%"],
["FX Fil Wet", "100%"]
]
default_parameters = {param[0]: param[1] for param in serum_default_parameters}

def safe_parse(input_text):
    pattern = re.compile(r'\[\s*(".*?"|\'.*?\')\s*,\s*(".*?"|\'.*?\'|\d+)\s*\]')
    matches = pattern.findall(input_text)
    return [[json.loads(item) for item in match] for match in matches]

def message_handler(address, *args):
    base_prompt = '''Interpret the user’s request with creativity within the specified ranges and default values, leveraging sound design knowledge to produce engaging and innovative soundscapes using the provided Serum VST parameters. While every response should include all 123 parameters in order formatted as [“Parameter Name”, “Value”] in a consistent list, allow for variations that reflect musicality and style. The user's request will be inputted at the bottom of this prompt.
Follow these guidelines:
Use the full spectrum of provided values and descriptions to address specific or abstract prompts (e.g., “bright and plucky,” “deep and textured”) while staying within bounds.
Be imaginative in assigning values to create sound textures that meet the user's description, but adhere strictly to parameter names and ensure all 123 parameters are included every time.
Return the parameters in the format [“Parameter Name”, “Value”], even if a parameter’s default value remains unchanged.
Here are the 123 parameters and their default values:
["Env1 Atk", "0.5 ms"],
["Env1 Hold", "0.0 ms"],
["Env1 Dec", "1.00 s"],
["Env1 Sus", "0.0 dB"],
["Env1 Rel", "15 ms"],
["Osc A On", "on"],
["A UniDet", "0.25"],
["A UniBlend", "75"],
["A WTPos", "Sine"],
["A Pan", "0"],
["A Vol", "75%"],
["A Unison", "1"],
["A Octave", "0 Oct"],
["A Semi", "0 semitones"],
["A Fine", "0 cents"],
["Fil Type", "MG Low 12"],
["Fil Cutoff", "425 Hz"],
["Fil Reso", "10%"],
["Filter On", "off"],
["Fil Driv", "0%"],
["Fil Var", "0%"],
["Fil Mix", "100%"],
["OscA>Fil", "on"],
["OscB>Fil", "off"],
["OscN>Fil", "off"],
["OscS>Fil", "off"],
["Osc N On", "off"],
["Noise Pitch", "50%"],
["Noise Level", "25%"],
["Osc S On", "off"],
["Sub Osc Level", "75%"],
["SubOscOctave", "0 Oct"],
["SubOscShape", "Sine"],
["Osc B On", "off"],
["B UniDet", "0.25"],
["B UniBlend", "75"],
["B WTPos", "1"],
["B Pan", "0"],
["B Vol", "75%"],
["B Unison", "1"],
["B Octave", "0 Oct"],
["B Semi", "0 semitones"],
["B Fine", "0 cents"],
["Hyp Enable", "off"],
["Hyp_Rate", "40%"],
["Hyp_Detune", "25%"],
["Hyp_Retrig", "off"],
["Hyp_Wet", "50%"],
["Hyp_Unision", "4"],
["HypDim_Size", "50%"],
["HypDim_Mix", "0%"],
["Dist Enable", "off"],
["Dist_Mode", "Tube"],
["Dist_PrePost", "Off"],
["Dist_Freq", "330 Hz"],
["Dist_BW", "1.9"],
["Dist_L/B/H", "0%"],
["Dist_Drv", "25%"],
["Dist_Wet", "100%"],
["Flg Enable", "off"],
["Flg_Rate", "0.08 Hz"],
["Flg_BPM_Sync", "off"],
["Flg_Dep", "100%"],
["Flg_Feed", "50%"],
["Flg_Stereo", "180deg."],
["Flg_Wet", "100%"],
["Phs Enable", "off"],
["Phs_Rate", "0.08 Hz"],
["Phs_BPM_Sync", "off"],
["Phs_Dpth", "50%"],
["Phs_Frq", "600 Hz"],
["Phs_Feed", "80%"],
["Phs_Stereo", "180deg."],
["Phs_Wet", "100%"],
["Cho Enable", "off"],
["Cho_Rate", "0.08 Hz"],
["Cho_BPM_Sync", "off"],
["Cho_Dly", "5.0 ms"],
["Cho_Dly2", "0.0 ms"],
["Cho_Dep", "26.0 ms"],
["Cho_Feed", "10%"],
["Cho_Filt", "1000 Hz"],
["Cho_Wet", "50%"],
["Dly Enable", "off"],
["Dly_Feed", "40%"],
["Dly_BPM_Sync", "on"],
["Dly_Link", "Unlink, Link"],
["Dly_TimL", "1/4"],
["Dly_TimR", "1/4"],
["Dly_BW", "6.8"],
["Dly_Freq", "849 Hz"],
["Dly_Mode", "Normal"],
["Dly_Wet", "30%"],
["Comp Enable", "off"],
["Cmp_Thr", "-18.1 dB"],
["Cmp_Att", "90.1 ms"],
["Cmp_Rel", "90 ms"],
["CmpGain", "0.0 dB"],
["CmpMBnd", "Normal"],
["Comp_Wet", "100"],
["Rev Enable", "off"],
["VerbSize", "35%"],
["Decay", "4.7 s"],
["VerbLoCt", "0%"],
["VerbHiCt", "35%"],
["Spin Rate", "25%"],
["Verb Wet", "20%"],
["EQ Enable", "off"],
["EQ FrqL", "210 Hz"],
["EQ Q L", "60%"],
["EQ VolL", "0.0 dB"],
["EQ TypL", "Shelf"],
["EQ TypeH", "Shelf"],
["EQ FrqH", "2041 Hz"],
["EQ Q H", "60%"],
["EQ VolH", "0.0"],
["FX Fil Enable", "off"],
["FX Fil Type", "MG Low 6"],
["FX Fil Freq", "330 Hz"],
["FX Fil Reso", "0%"],
["FX Fil Drive", "0%"],
["FX Fil Pan", "50%"],
["FX Fil Wet", "100%"]
]
Here are those 123 parameter’s respective ranges that you can choose from:
[
    ["Env1 Atk", "0.0 ms - 32.0 s"],
    ["Env1 Hold", "0.0 ms - 32.0 s"],
    ["Env1 Dec", "0.0 ms - 32.0 s"],
    ["Env1 Sus", "-inf dB - 0.0 dB"],
    ["Env1 Rel", "0.0ms - 32.0s"],
    ["Osc A On", "off, on"],
    ["A UniDet", "0.00 - 1.00"],
    ["A UniBlend", "0 - 100"],
    ["A WTPos", "Sine, Saw, Triangle, Square, Pulse, Half Pulse, Inv-Phase Saw"],
    ["A Pan", "-50 - 50"],
    ["A Vol", "0% - 100%"],
    ["A Unison", "1 - 16"],
    ["A Octave", "-4 Oct, -3 Oct, -2 Oct, -1 Oct, 0 Oct, 1 Oct, 2 Oct, 3 Oct, 4 Oct"],
    ["A Semi", "-12 semitones - +12 semitones"],
    ["A Fine", "-100 cents - 100 cents"],
    ["Fil Type", "MG Low 6, MG Low 12, MG Low 18, MG Low 24, Low 6, Low 12, Low 18, Low 24, High 6, High 12, High 18, High 24, Band 12, Band 24, Peak 12, Peak 24, Notch 12, Notch 24, LH 6, LH 12, LB 12, LP 12, LN 12, HB 12, HP 12, HN 12, BP 12, PP 12, PN 12, NN 12, L/B/H 12, L/B/H 24, L/P/H 12, L/P/H 24, L/N/H 12, L/N/H 24, B/P/N 12, B/P/N 24, Cmb +, Cmb -, Cmb L6+, Cmb L6-, Cmb H6+, Cmb H6-, Cmb HL6+, Cmb HL6-, Flg +, Flg -, Flg L6+, Flg L6-, Flg H6+, Flg H6-, Flg HL6+, Flg HL6-, Phs 12+, Phs 12-, Phs 24+, Phs 24-, Phs 36+, Phs 36-, Phs 48+, Phs 48-, Phs 48L6+, Phs 48L6-, Phs 48H6+, Phs 48H6-, Phs 48HL6+, Phs 48HL6-, FPhs 12HL6+, FPhs 12HL6-, Low EQ 6, Low EQ 12, Band EQ 12, High EQ 6, High EQ 12, Ring Mod, Ring Modx2, SampHold, SampHold-, Combs, Allpasses, Reverb, French LP, German LP, Add Bass, Formant-I, Formant-II, Formant-III, Bandreject, Dist.Comb 1 LP, Dist.Comb 1 BP, Dist.Comb 2 LP, Dist.Comb 2 BP, Scream LP, Scream BP"],
    ["Fil Cutoff", "8 Hz - 22050 Hz"],
    ["Fil Reso", "0% - 100%"],
    ["Filter On", "off, on"],
    ["Fil Driv", "0% - 100%"],
    ["Fil Var", "0% - 100%"],
    ["Fil Mix", "0% - 100%"],
    ["OscA>Fil", "off, on"],
    ["OscB>Fil", "off, on"],
    ["OscN>Fil", "off, on"],
    ["OscS>Fil", "off, on"],
    ["Osc N On", "off, on"],
    ["Noise Pitch", "0% - 100%"],
    ["Noise Level", "0% - 100%"],
    ["Osc S On", "off, on"],
    ["Sub Osc Level", "0%-100%"],
    ["SubOscOctave", "-4 Oct, -3 Oct, -2 Oct, -1 Oct, 0 Oct, 1 Oct, 2 Oct, 3 Oct, 4 Oct"],
    ["SubOscShape", "Sine, RoundRect, Triangle, Saw, Square, Pulse"],
    ["Osc B On", "off, on"],
    ["B UniDet", "0.00 - 1.00"],
    ["B UniBlend", "0 - 100"],
    ["B WTPos", "Sine, Saw, Triangle, Square, Pulse, Half Pulse, Inv-Phase Saw"],
    ["B Pan", "-50 - 50"],
    ["B Vol", "0% - 100%"],
    ["B Unison", "1 - 16"],
    ["B Octave", "-4 Oct, -3 Oct, -2 Oct, -1 Oct, 0 Oct, 1 Oct, 2 Oct, 3 Oct, 4 Oct"],
    ["B Semi", "-12 semitones - +12 semitones"],
    ["B Fine", "-100 cents - 100 cents"],
    ["Hyp Enable", "off, on"],
    ["Hyp_Rate", "0% - 100%"],
    ["Hyp_Detune", "0% - 100%"],
    ["Hyp_Retrig", "off - Retrig"],
    ["Hyp_Wet", "0% - 100%"],
    ["Hyp_Unision", "0 - 7"],
    ["HypDim_Size", "0% - 100%"],
    ["HypDim_Mix", "0% - 100%"],
    ["Dist Enable", "off, on"],
    ["Dist_Mode", "Tube, SoftClip, HardClip, Diode 1, Diode 2, Lin.Fold, Sin Fold, Zero-Square, Downsample, Asym, Rectify, X-Shaper, X-Shaper (Asym), Sine Shaper, Stomp Box, Tape Stop"],
    ["Dist_PrePost", "Off, Pre, Post"],
    ["Dist_Freq", "8 Hz, 13290 Hz"],
    ["Dist_BW", "0.1 - 7.6"],
    ["Dist_L/B/H", "0% - 100%"],
    ["Dist_Drv", "0% - 100%"],
    ["Dist_Wet", "0% - 100%"],
    ["Flg Enable", "off, on"],
    ["Flg_Rate", "0.00 Hz - 20.00 Hz"],
    ["Flg_BPM_Sync", "off, on"],
    ["Flg_Dep", "0% - 100%"],
    ["Flg_Feed", "0% - 100%"],
    ["Flg_Stereo", "22 Hz - 200"],
    ["Flg_Wet", "0% - 100%"],
    ["Phs Enable", "off, on"],
    ["Phs_Rate", "0.00 Hz - 20.00 Hz"],
    ["Phs_BPM_Sync", "off, on"],
    ["Phs_Dpth", "0% - 100%"],
    ["Phs_Frq", "20 Hz - 18000 Hz"],
    ["Phs_Feed", "0% - 100%"],
    ["Phs_Stereo", "0 deg. - 360 deg."],
    ["Phs_Wet", "0% - 100%"],
    ["Cho Enable", "off, on"],
    ["Cho_Rate", "0.00 Hz - 20.00 Hz"],
    ["Cho_BPM_Sync", "off, on"],
    ["Cho_Dly", "0.0 ms - 20.0 ms"],
    ["Cho_Dly2", "0.0 ms - 20.0 ms"],
    ["Cho_Dep", "0.0 ms - 26.0 ms"],
    ["Cho_Feed", "0% - 95%"],
    ["Cho_Filt", "50 Hz - 20000 Hz"],
    ["Cho_Wet", "0% - 100%"],
    ["Dly Enable", "off, on"],
    ["Dly_Feed", "0% - 100%"],
    ["Dly_BPM_Sync", "off, on"],
    ["Dly_Link", "Unlink, Link"],
    ["Dly_TimL", "If Dly_BPM_Sync on, Dly_TimL and Dly_TimR will be on [fast, 1/256, 1/128, 1/64, 1/32, 1/16, 1/8, 1/4, 1/2, bar, 2 bar, 4 bar]. If off: [1.00 - 501.00]"],
    ["Dly_TimR", "If Dly_BPM_Sync on, Dly_TimL and Dly_TimR will be on [fast, 1/256, 1/128, 1/64, 1/32, 1/16, 1/8, 1/4, 1/2, bar, 2 bar, 4 bar]. If off: [1.00 - 501.00]"],
    ["Dly_BW", ".8 - 8.2"],
    ["Dly_Freq", "40 Hz - 18000 Hz"],
    ["Dly_Mode", "Normal, Ping-Pong, Tap->Delay"],
    ["Dly_Wet", "0% - 100%"],
    ["Comp Enable", "off, on"],
    ["Cmp_Thr", "0.0 dB - 120.0 dB"],
    ["Cmp_Att", "0.1 ms - 1000.0 ms"],
    ["Cmp_Rel", "0.1 ms - 999.1 ms"],
    ["CmpGain", "0.0 dB - 30.1 dB"],
    ["CmpMBnd", "Normal, MultBand"],
    ["Comp_Wet", "0 - 100"],
    ["Rev Enable", "off, on"],
    ["VerbSize", "0% - 100%"],
    ["Decay", "0.8 s - 12.0 s"],
    ["VerbLoCt", "0% - 100%"],
    ["VerbHiCt", "0% - 100%"],
    ["Spin Rate", "0% - 100%"],
    ["Verb Wet", "0% - 100%"],
    ["EQ Enable", "off, on"],
    ["EQ FrqL", "22 Hz - 20000 Hz"],
    ["EQ Q L", "0% - 100%"],
    ["EQ VolL", "-24.0 dB - 24.0 dB"],
    ["EQ TypL", "Shelf, Peak, LPF"],
    ["EQ TypeH", "Shelf, Peak, LPF"],
    ["EQ FrqH", "22 Hz - 20000 Hz"],
    ["EQ Q H", "0% - 100%"],
    ["EQ VolH", "-24.0 dB - 24.0 dB"],
    ["FX Fil Enable", "off, on"],
    ["FX Fil Type", "MG Low 6, MG Low 12, MG Low 18, MG Low 24, Low 6, Low 12, Low 18, Low 24, High 6, High 12, High 18, High 24, Band 12, Band 24, Peak 12, Peak 24, Notch 12, Notch 24, LH 6, LH 12, LB 12, LP 12, LN 12, HB 12, HP 12, HN 12, BP 12, PP 12, PN 12, NN 12, L/B/H 12, L/B/H 24, L/P/H 12, L/P/H 24, L/N/H 12, L/N/H 24, B/P/N 12, B/P/N 24, Cmb +, Cmb -, Cmb L6+, Cmb L6-, Cmb H6+, Cmb H6-, Cmb HL6+, Cmb HL6-, Flg +, Flg -, Flg L6+, Flg L6-, Flg H6+, Flg H6-, Flg HL6+, Flg HL6-, Phs 12+, Phs 12-, Phs 24+, Phs 24-, Phs 36+, Phs 36-, Phs 48+, Phs 48-, Phs 48L6+, Phs 48L6-, Phs 48H6+, Phs 48H6-, Phs 48HL6+, Phs 48HL6-, FPhs 12HL6+, FPhs 12HL6-, Low EQ 6, Low EQ 12, Band EQ 12, High EQ 6, High EQ 12, Ring Mod, Ring Modx2, SampHold, SampHold-, Combs, Allpasses, Reverb, French LP, German LP, Add Bass, Formant-I, Formant-II, Formant-III, Bandreject, Dist.Comb 1 LP, Dist.Comb 1 BP, Dist.Comb 2 LP, Dist.Comb 2 BP, Scream LP, Scream BP"],
    ["FX Fil Freq", "18 Hz - 13290 Hz"],
    ["FX Fil Reso", "0% - 100%"],
    ["FX Fil Drive", "0% - 100%"],
    ["FX Fil Pan", "0% - 100%"],
    ["FX Fil Wet", "0% - 100%"]
]
To facilitate accurate parsing and handling of your requests, please provide parameter adjustments in JSON format when possible. This ensures the correct interpretation and application of your specifications.
User request:
'''



    global last_trigger_time
    current_time = time.time()
    if current_time - last_trigger_time >= trigger_interval:
        last_trigger_time = current_time

        if args and args[0] == "text":
            args = args[1:]  # Remove the "text" label from the arguments
        combined_text = ' '.join(map(str, args))

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": base_prompt},
                {"role": "user", "content": combined_text}
            ],
            max_tokens=2000
        )
        generated_text = response.choices[0].message['content'].strip()
        '''generated_text =\
    [
    ["Env1 Atk", "2.0 s"],
    ["Env1 Hold", "3.0 s"],
    ["Env1 Dec", "3.0 s"],
    ["Env1 Sus", "-6.0 dB"],
    ["Env1 Rel", "2.0 s"],
    ["Osc A On", "on"],
    ["A UniDet", "0.50"],
    ["A UniBlend", "50"],
    ["A WTPos", "4"],
    ["A Pan", "0"],
    ["A Vol", "100% (0.0 dB)"],
    ["A Unison", "4"],
    ["A Octave", "0 Oct"],
    ["A Semi", "0 semitones"],
    ["A Fine", "0 cents"],
    ["Fil Type", "MG Low 12"],
    ["Fil Cutoff", "8000 Hz"],
    ["Fil Reso", "50%"],
    ["Filter On", "on"],
    ["Fil Driv", "0%"],
    ["Fil Var", "0%"],
    ["Fil Mix", "100%"],
    ["OscA>Fil", "on"],
    ["OscB>Fil", "off"],
    ["OscN>Fil", "off"],
    ["OscS>Fil", "off"],
    ["Osc N On", "off"],
    ["Noise Pitch", "0%"],
    ["Noise Level", "0% (-inf dB)"],
    ["Osc S On", "off"],
    ["Sub Osc Level", "0%"],
    ["SubOscOctave", "0 Oct"],
    ["SubOscShape", "Sine"],
    ["Osc B On", "off"],
    ["B UniDet", "0.00"],
    ["B UniBlend", "0"],
    ["B WTPos", "1"],
    ["B Pan", "0"],
    ["B Vol", "0% (-inf dB)"],
    ["B Unison", "1"],
    ["B Octave", "0 Oct"],
    ["B Semi", "0 semitones"],
    ["B Fine", "0 cents"],
    ["Hyp Enable", "off"],
    ["Hyp_Rate", "0%"],
    ["Hyp_Detune", "0%"],
    ["Hyp_Retrig", "off"],
    ["Hyp_Wet", "0%"],
    ["Hyp_Unision", "0"],
    ["HypDim_Size", "0%"],
    ["HypDim_Mix", "0%"],
    ["Dist Enable", "off"],
    ["Dist_Mode", "Tube"],
    ["Dist_PrePost", "Off"],
    ["Dist_Freq", "8 Hz"],
    ["Dist_BW", "0.1"],
    ["Dist_L/B/H", "0%"],
    ["Dist_Drv", "0%"],
    ["Dist_Wet", "0%"],
    ["Flg Enable", "off"],
    ["Flg_Rate", "0.00 Hz"],
    ["Flg_BPM_Sync", "off"],
    ["Flg_Dep", "0%"],
    ["Flg_Feed", "0%"],
    ["Flg_Stereo", "22 Hz"],
    ["Flg_Wet", "0%"],
    ["Phs Enable", "off"],
    ["Phs_Rate", "0.00 Hz"],
    ["Phs_BPM_Sync", "off"],
    ["Phs_Dpth", "0%"],
    ["Phs_Frq", "20 Hz"],
    ["Phs_Feed", "0%"],
    ["Phs_Stereo", "0 deg."],
    ["Phs_Wet", "0%"],
    ["Cho Enable", "off"],
    ["Cho_Rate", "0.00 Hz"],
    ["Cho_BPM_Sync", "off"],
    ["Cho_Dly", "0.0 ms"],
    ["Cho_Dly2", "0.0 ms"],
    ["Cho_Dep", "0.0 ms"],
    ["Cho_Feed", "0%"],
    ["Cho_Filt", "50 Hz"],
    ["Cho_Wet", "0%"],
    ["Dly Enable", "off"],
    ["Dly_Feed", "0%"],
    ["Dly_BPM_Sync", "off"],
    ["Dly_Link", "Unlink"],
    ["Dly_TimL", "1.00"],
    ["Dly_TimR", "1.00"],
    ["Dly_BW", "0.8"],
    ["Dly_Freq", "40 Hz"],
    ["Dly_Mode", "Normal"],
    ["Dly_Wet", "0%"],
    ["Comp Enable", "off"],
    ["Cmp_Thr", "0.0 dB"],
    ["Cmp_Att", "0.1 ms"],
    ["Cmp_Rel", "0.1 ms"],
    ["CmpGain", "0.0 dB"],
    ["CmpMBnd", "Normal"],
    ["Comp_Wet", "0"],
    ["Rev Enable", "off"],
    ["VerbSize", "0%"],
    ["Decay", "0.8 s"],
    ["VerbLoCt", "0%"],
    ["VerbHiCt", "0%"],
    ["Spin Rate", "0%"],
    ["Verb Wet", "0%"],
    ["EQ Enable", "off"],
    ["EQ FrqL", "22 Hz"],
    ["EQ Q L", "0%"],
    ["EQ VolL", "-24.0 dB"],
    ["EQ TypL", "Shelf"],
    ["EQ TypeH", "Shelf"],
    ["EQ FrqH", "22 Hz"],
    ["EQ Q H", "0%"],
    ["EQ VolH", "-24.0 dB"],
    ["FX Fil Enable", "off"],
    ["FX Fil Type", "MG Low 12"],
    ["FX Fil Freq", "8000 Hz"],
    ["FX Fil Reso", "50%"],
    ["FX Fil Drive", "0%"],
    ["FX Fil Pan", "0%"],
    ["FX Fil Wet", "0%"]
    ]'''
        #print("initial Response:", generated_text)
        try:
            parameter_list = json.loads(generated_text)
        except json.JSONDecodeError:
            print("Failed to parse as JSON. Trying safe parse as a fallback.")
            parameter_list = safe_parse(generated_text)
        if isinstance(parameter_list, list):
            for item in parameter_list:
                if isinstance(item, list) and len(item) == 2:
                    name, value = item
                    if isinstance(name, str) and name in default_parameters:
                        default_parameters[name] = value
        final_parameter_list = [[name, value] for name, value in default_parameters.items()]
        for i in final_parameter_list:
            print(i)
        def send_osc(port, data):
            client = udp_client.SimpleUDPClient("127.0.0.1", port)
            client.send_message("/param1", data)

        def get_random_midi_value() -> int:
            return random.randint(1, 127)
        def get_random_small_midi_value() -> int:
            return random.randint(1, 40)
        def get_random_macro_value() -> int:
            return random.randint(0, 100)
        def normalize_ms_s(input_str: str) -> int:
            serum_values = [
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.1, 0.2, 0.2, 0.4, 0.5, 0.7, 1.0, 1.4, 1.8, 2.4, 3.1, 4.0,
                5.0, 6.2, 7.7, 9.5, 12, 14, 17, 20, 24, 28, 32, 38, 44, 51, 59, 67, 77, 87, 99, 112, 127, 142, 160, 179,
                199,
                222, 247, 274, 303, 334, 368, 405, 445, 487, 533, 583, 636, 692, 753, 818, 887, 961, 1040, 1120, 1210,
                1310,
                1410, 1510, 1630, 1750, 1870, 2010, 2150, 2300, 2460, 2620, 2800, 2980, 3170, 3380, 3590, 3820, 4050,
                4300,
                4560, 4830, 5110, 5410, 5720, 6040, 6380, 6740, 7110, 7490, 7900, 8320, 8760, 9210, 9690, 10200, 10700,
                11200,
                11800, 12400, 13000, 13600, 14200, 14900, 15600, 16300, 17100, 17800, 18600, 19500, 20300, 21200, 22200,
                23100, 24100, 25100, 26200, 27300, 28400, 29600, 30800, 32000
            ]
            midi_values = range(1, 128)
            match = re.match(r'([+-]?[0-9]*\.?[0-9]+)\s*(ms|s)', input_str.strip())
            if not match:
                return get_random_small_midi_value()
                #Unlikely that random values get used, but they're here just incase there is an error
            value = float(match.group(1))
            unit = match.group(2)
            if unit == 's':
                value_in_ms = value * 1000
            elif unit == 'ms':
                value_in_ms = value
            else:
                return get_random_small_midi_value()
            for i, serum_value in enumerate(serum_values):
                if value_in_ms <= serum_value:
                    return midi_values[i]
            return 127
        def normalize_dB_to_midi(input_str: str) -> int:
            dB_values = [
                float('-inf'), -84.2, -72.1, -65.1, -60.1, -56.2, -53.0, -50.3, -48.0, -46.0, -44.2, -42.5, -41.0,
                -39.6,
                -38.3, -37.1, -36.0, -34.9, -33.9, -33.0, -32.1, -31.3, -30.5, -29.7, -28.9, -28.2, -27.6, -26.9, -26.3,
                -25.7, -25.1, -24.5, -23.9, -23.4, -22.9, -22.4, -21.9, -21.4, -21.0, -20.5, -20.1, -19.6, -19.2, -18.8,
                -18.4, -18.0, -17.6, -17.3, -16.9, -16.5, -16.2, -15.8, -15.5, -15.2, -14.9, -14.5, -14.2, -13.9, -13.6,
                -13.3, -13.0, -12.7, -12.5, -12.2, -11.9, -11.6, -11.4, -11.1, -10.9, -10.6, -10.3, -10.1, -9.9, -9.6,
                -9.4, -9.1, -8.9, -8.7, -8.5, -8.2, -8.0, -7.8, -7.6, -7.4, -7.2, -7.0, -6.8, -6.6, -6.4, -6.2, -6.0,
                -5.8, -5.6, -5.4, -5.2, -5.0, -4.9, -4.7, -4.5, -4.3, -4.2, -4.0, -3.8, -3.6, -3.5, -3.3, -3.1, -3.0,
                -2.8, -2.7, -2.5, -2.3, -2.2, -2.0, -1.9, -1.7, -1.6, -1.4, -1.3, -1.1, -1.0, -0.8, -0.7, -0.6, -0.4,
                -0.3, -0.1, 0.0
            ]
            midi_values = range(0, 128)
            if input_str == '-inf dB':
                value_in_dB = float('-inf')
            else:
                match = re.match(r'([+-]?[0-9]*\.?[0-9]+)\s*dB', input_str.strip())
                if not match:
                    raise ValueError("Invalid input format. Must be a string containing a float followed by 'dB'.")
                value_in_dB = float(match.group(1))
            for i, dB_value in enumerate(dB_values):
                if value_in_dB <= dB_value:
                    return midi_values[i]
            return 127
        def normalize_pan_to_midi(input_str: str) -> int:
            try:
                pan_value = float(input_str)
            except ValueError:
                return get_random_midi_value()
            midi_value = int(round(((pan_value + 50) / 100) * 126 + 1))
            return max(1, min(127, midi_value))
        def cho_depth_to_percentage(input_str: str) -> int:
            try:
                ms_value = float(input_str.replace(" ms", ""))
            except ValueError:
                return get_random_macro_value()
            ms_to_percentage_map = {
                0.0: 0, 0.1: 5, 0.2: 8, 0.3: 10, 0.4: 12, 0.5: 14, 0.6: 15, 0.7: 16, 0.8: 17, 0.9: 19,
                1.0: 20, 1.1: 21, 1.3: 22, 1.4: 23, 1.5: 24, 1.6: 25, 1.8: 26, 1.9: 27, 2.0: 28, 2.2: 29,
                2.3: 30, 2.5: 31, 2.7: 32, 2.8: 33, 3.0: 34, 3.2: 35, 3.4: 36, 3.6: 37, 3.8: 38, 4.0: 39,
                4.2: 40, 4.4: 41, 4.6: 42, 4.8: 43, 5.0: 44, 5.4: 45, 5.5: 46, 5.7: 47, 6.0: 48, 6.2: 49,
                6.5: 50, 6.8: 51, 7.0: 52, 7.3: 53, 7.6: 54, 7.9: 55, 8.2: 56, 8.4: 57, 8.9: 58, 9.2: 59,
                9.4: 60, 9.7: 61, 10.0: 62, 10.3: 63, 10.6: 64, 11.0: 65, 11.3: 66, 11.7: 67, 12.0: 68,
                12.4: 69, 12.7: 70, 13.1: 71, 13.5: 72, 13.9: 73, 14.4: 74, 14.6: 75, 15.0: 76, 15.4: 77,
                15.8: 78, 16.2: 79, 16.6: 80, 17.1: 81, 17.5: 82, 17.9: 83, 18.3: 84, 18.8: 85, 19.2: 86,
                19.7: 87, 20.1: 88, 20.8: 89, 21.1: 90, 21.5: 91, 22.0: 92, 22.5: 93, 23.0: 94, 23.5: 95,
                24.0: 96, 24.5: 97, 25.0: 98, 25.7: 99, 26.0: 100
            }
            if ms_value in ms_to_percentage_map:
                return ms_to_percentage_map[ms_value]
            lower_bound = max(k for k in ms_to_percentage_map if k <= ms_value)
            upper_bound = min(k for k in ms_to_percentage_map if k > ms_value)
            lower_percentage = ms_to_percentage_map[lower_bound]
            upper_percentage = ms_to_percentage_map[upper_bound]
            interpolated_percentage = lower_percentage + ((ms_value - lower_bound) / (upper_bound - lower_bound)) * (
                    upper_percentage - lower_percentage)
            return round(interpolated_percentage, 1)
        def wt_to_midi(wt):
            wt_to_midi_map = {
                "1": 10,
                "2": 20,
                "3": 50,
                "4": 60,
                "5": 75,
                "6": 95,
                "7": 127,
                "Sine": 10,
                "Saw": 20,
                "Triangle": 50,
                "Square": 60,
                "Pulse":75,
                "Half Pulse":95,
                "Inv-Phase saw": 127
            }
            if wt not in wt_to_midi_map:
                return get_random_midi_value()
            return wt_to_midi_map[wt]
        def wt_to_macro(wt):
            wt_macro_map = {
                '1': 14,
                '2': 18,
                '3': 30,
                '4': 45,
                '5': 59,
                '6': 74,
                '7': 100
            }
            return wt_macro_map.get(wt)
        def unison_to_midi(uni):
            uni_to_midi_map = {
                "1": 0,
                "2": 6,
                "3": 19,
                "4": 29,
                "5": 31,
                "6": 45,
                "7": 48,
                "8": 58,
                "9": 68,
                "10": 74,
                "11": 82,
                "12": 90,
                "13": 105,
                "14": 113,
                "15": 117,
                "16": 127
            }
            if uni not in uni_to_midi_map:
                return get_random_midi_value()
            return uni_to_midi_map[uni]
        def unison_to_macro(uni):
            uni_to_macro_map = {
                "1": 0,
                "2": 4,
                "3": 11,
                "4": 19,
                "5": 25,
                "6": 33,
                "7": 37,
                "8": 44,
                "9": 54,
                "10": 60,
                "11": 65,
                "12": 70,
                "13": 80,
                "14": 85,
                "15": 90,
                "16": 100
            }
            if uni not in uni_to_macro_map:
                return get_random_midi_value()
            return uni_to_macro_map[uni]
        def percentage_to_macro(percentage_str):
            try:
                return int(percentage_str.strip('%'))
            except ValueError:
                return get_random_macro_value()
        def percentage_to_midi(percentage_str):
            try:
                percentage = int(percentage_str.strip('%'))
                if not 0 <= percentage <= 100:
                    return get_random_macro_value()
                midi_value = int((percentage / 100) * 127)
                return midi_value
            except ValueError:
                return get_random_macro_value()
        def oct_to_macro(oct):
            oct_to_macro_map = {
                "-4 Oct": 0,
                "-3 Oct": 10,
                "-2 Oct": 20,
                "-1 Oct": 35,
                "0 Oct": 45,
                "+1 Oct": 60,
                "+2 Oct": 70,
                "+3 Oct": 85,
                "+4 Oct": 100
            }
            if oct not in oct_to_macro_map:
                return get_random_macro_value()
            return oct_to_macro_map[oct]
        def oct_to_midi(oct):
            oct_to_midi_map = {
                "-4 Oct": 0,
                "-3 Oct": 13,
                "-2 Oct": 26,
                "-1 Oct": 40,
                "0 Oct": 60,
                "+1 Oct": 81,
                "+2 Oct": 98,
                "+3 Oct": 108,
                "+4 Oct": 127
            }
            if oct not in oct_to_midi_map:
                return get_random_midi_value()
            return oct_to_midi_map[oct]
        def semi_to_macro(semi):
            semi = semi.replace(" semitones", "").strip()
            semi_to_macro_map = {
                "-12": 0,
                "-11": 3,
                "-10": 7,
                "-9": 11,
                "-8": 15,
                "-7": 20,
                "-6": 26,
                "-5": 30,
                "-4": 35,
                "-3": 37,
                "-2": 40,
                "-1": 45,
                "0": 50,
                "+1": 55,
                "+2": 60,
                "+3": 62,
                "+4": 65,
                "+5": 70,
                "+6": 75,
                "+7": 80,
                "+8": 85,
                "+9": 87,
                "+10": 90,
                "+11": 95,
                "+12": 100
            }
            if semi not in semi_to_macro_map:
                return get_random_macro_value()
            return semi_to_macro_map[semi]
        def fine_to_macro(cents_str):
            try:
                cents = cents_str.replace(" cents", "").strip()
                cents = int(cents)
                if cents < -100 or cents > 100:
                    return get_random_macro_value()
                normalized_value = (cents + 100) / 200 * 100.0
                return round(normalized_value, 1)
            except:
                return get_random_macro_value()
        def uni_det_to_macro(intensity_str):
            intensity = float(intensity_str)
            if intensity < 0.0 or intensity > 1.0:
                return get_random_macro_value()
            if intensity == 0:
                return 0.0
            normalized_value = (intensity ** 0.5) * 100
            return round(normalized_value, 1)
        def filter_type_to_macro(filter_name):
            filter_percentages = {
                "MG Low 6": 0.00, "MG Low 12": 0.79, "MG Low 18": 2.36, "MG Low 24": 3.15,
                "Low 6": 3.94, "Low 12": 5.51, "Low 18": 6.30, "Low 24": 7.09,
                "High 6": 8.66, "High 12": 9.45, "High 18": 10.2, "High 24": 11.8,
                "Band 12": 12.6, "Band 24": 13.4, "Peak 12": 15.0, "Peak 24": 15.7,
                "Notch 12": 16.5, "Notch 24": 18.1, "LH 6": 18.9, "LH 12": 19.7,
                "LB 12": 21.3, "LP 12": 22.0, "LN 12": 22.8, "HB 12": 24.4,
                "HP 12": 25.2, "HN 12": 26.0, "BP 12": 27.6, "PP 12": 29.1,
                "PN 12": 30.7, "NN 12": 31.5, "L/B/H 12": 32.3, "L/B/H 24": 33.9,
                "L/P/H 12": 34.6, "L/P/H 24": 35.4, "L/N/H 12": 37.0, "L/N/H 24": 37.8,
                "B/P/N 12": 38.6, "B/P/N 24": 40.2, "Cmb +": 40.9, "Cmb -": 41.7,
                "Cmb L6+": 43.3, "Cmb L6-": 44.1, "Cmb H6+": 44.9, "Cmb H6-": 46.5,
                "Cmb HL6+": 47.2, "Cmb HL6-": 48.0, "Flg +": 49.6, "Flg -": 50.4,
                "Flg L6+": 51.2, "Flg L6-": 52.8, "Flg H6+": 53.5, "Flg H6-": 54.3,
                "Flg HL6+": 55.9, "Flg HL6-": 56.7, "Phs 12+": 57.5, "Phs 12-": 59.1,
                "Phs 24+": 59.8, "Phs 24-": 60.6, "Phs 36+": 62.2, "Phs 36-": 63.0,
                "Phs 48+": 63.8, "Phs 48-": 65.4, "Phs 48L6+": 66.1, "Phs 48L6-": 66.9,
                "Phs 48H6+": 68.5, "Phs 48H6-": 69.3, "Phs 48HL6+": 70.1, "Phs 48HL6-": 71.7,
                "FPhs 12HL6+": 72.4, "FPhs 12HL6-": 73.2, "Low EQ 6": 74.8, "Low EQ 12": 75.6,
                "Band EQ 12": 76.4, "High EQ 6": 78.0, "High EQ 12": 78.7, "Ring Mod": 79.5,
                "Ring Modx2": 81.1, "SampHold": 81.9, "SampHold-": 82.7, "Combs": 84.3,
                "Allpasses": 85.0, "Reverb": 85.8, "French LP": 87.4, "German LP": 88.2,
                "Add Bass": 89.0, "Formant-I": 90.6, "Formant-II": 91.3, "Formant-III": 92.1,
                "Bandreject": 93.7, "Dist.Comb 1 LP": 94.5, "Dist.Comb 1 BP": 96.1,
                "Dist.Comb 2 LP": 96.9, "Dist.Comb 2 BP": 97.6, "Scream LP": 98.4,
                "Scream BP": 100.0
            }
            return filter_percentages.get(filter_name, get_random_macro_value())
        def distortion_type_to_macro(distortion_name):
            distortion_percentages = {
                "Tube": 0.00, "SoftClip": 3.94, "HardClip": 10.2, "Diode 1": 17.3,
                "Diode 2": 23.6, "Lin.Fold": 30.7, "Sin Fold": 37.0, "Zero-Square": 44.1,
                "Downsample": 50.4, "Asym": 56.7, "Rectify": 63.8, "X-Shaper": 70.1,
                "X-Shaper (Asym)": 77.2, "Sine Shaper": 83.5, "Stomp Box": 90.6, "Tape Stop.": 100.0
            }
            return distortion_percentages.get(distortion_name, get_random_macro_value())
        def cho_feed_to_macro(intensity_str):
            intensity = float(intensity_str.replace("%", ""))
            if intensity < 0.0 or intensity > 95.0:
                return get_random_macro_value()
            normalized_value = (intensity / 95.0) * 100.0
            return round(normalized_value, 1)
        def frequency_to_percentage(freq_str):
            frequency = float(freq_str.replace(" Hz", ""))
            freq_percentage_map = [
                (8, 0.00), (9, 0.79), (10, 2.36), (11, 3.94), (12, 4.72), (13, 5.51),
                (14, 7.09), (15, 8.66), (17, 9.45), (18, 10.2), (20, 11.0), (21, 11.8),
                (22, 12.6), (24, 13.4), (25, 14.2), (27, 15.0), (28, 15.7), (30, 16.5),
                (32, 17.3), (34, 18.1), (36, 18.9), (39, 19.7), (41, 20.5), (44, 21.3),
                (47, 22.0), (50, 22.8), (53, 23.6), (56, 24.4), (60, 25.2), (64, 26.0),
                (68, 26.8), (72, 27.6), (77, 28.3), (82, 29.1), (87, 29.9), (93, 30.7),
                (99, 31.5), (105, 32.3), (111, 33.1), (119, 33.9), (126, 34.6), (134, 35.4),
                (143, 36.2), (158, 37.0), (162, 37.8), (172, 38.6), (184, 39.4), (195, 40.2),
                (208, 40.9), (221, 41.7), (235, 42.5), (251, 43.3), (261, 44.1), (284, 44.9),
                (302, 45.7), (321, 46.5), (342, 47.2), (364, 48.0), (387, 49.6), (438, 50.4),
                (467, 51.2), (497, 52.0), (528, 52.8), (562, 53.5), (599, 54.3), (637, 55.1),
                (678, 55.9), (722, 56.7), (768, 57.5), (816, 58.3), (869, 59.1), (925, 59.8),
                (984, 60.6), (1047, 61.4), (1115, 62.2), (1186, 63.0), (1263, 63.8), (1344, 64.6),
                (1430, 65.4), (1522, 66.1), (1620, 66.9), (1724, 67.7), (1835, 68.5), (1952, 69.3),
                (2078, 70.1), (2209, 70.9), (2351, 71.7), (2503, 72.4), (2663, 73.2), (2834, 74.0),
                (3017, 74.8), (3210, 75.6), (3417, 76.4), (3636, 77.2), (3870, 78.0), (4119, 78.7),
                (4383, 79.5), (4665, 80.3), (4965, 81.1), (5284, 81.9), (5623, 82.7), (5979, 83.5),
                (6363, 84.3), (6772, 85.0), (7207, 85.8), (7670, 86.6), (8163, 87.4), (8688, 88.2),
                (9246, 89.0), (9840, 89.8), (10472, 90.6), (11145, 91.3), (11861, 92.1), (12623, 92.9),
                (13434, 93.7), (14298, 94.5), (15216, 95.3), (16194, 96.1), (17219, 96.9), (18326, 97.6),
                (19503, 98.4), (20756, 99.2), (22050, 100.0)
            ]
            frequencies, percentages = zip(*freq_percentage_map)
            pos = bisect.bisect_left(frequencies, frequency)
            if pos == 0:
                return percentages[0]
            elif pos >= len(frequencies):
                return percentages[-1]
            f_low, f_high = frequencies[pos - 1], frequencies[pos]
            p_low, p_high = percentages[pos - 1], percentages[pos]
            interpolated_percentage = p_low + (p_high - p_low) * ((frequency - f_low) / (f_high - f_low))
            return round(interpolated_percentage, 1)
        def on_to_percentage(onoff):
            if onoff == "On" or onoff == "ON" or onoff == "on" or onoff == "retrig" or onoff == "link" or onoff == "LINK" or onoff == "Link" or onoff == "1":
                return 50
            if onoff == "Off" or onoff == "off" or onoff == "OFF" or onoff == "Unlink" or onoff == "unlink" or onoff == "UNLINK" or onoff == "0":
                return 0
            try:
                if int(onoff):
                    return 1
                else:
                    return 0
            except:
                return get_random_macro_value()
        def CmpMBnd_to_percentage(onoff):
            if onoff == "Multiband" or onoff == "multiband" or onoff == "mb" or onoff == "MULTIBAND" or onoff == "MB" or onoff == "MultiBand" or onoff == "1":
                return 100
            elif onoff == "Normal" or onoff == "normal" or onoff == "NORMAL" or onoff == "0":
                return 0
            return get_random_macro_value()
        def sub_shape_to_macro(shape_name):
            sub_osc_shape_percentages = {
                "Sine": 0,
                "RoundRect": 12,
                "Triangle": 32,
                "Saw": 52,
                "Square": 75,
                "Pulse": 100
            }
            return sub_osc_shape_percentages.get(shape_name, get_random_macro_value())
        def hyp_unison_to_macro(value):
            value = int(value)
            if value < 0 or value > 7:
                return get_random_macro_value()
            return (value / 7) * 100
        def dist_pre_post_to_macro(setting):
            settings = {
                "Off": 8,
                "Pre": 35,
                "Post": 100,
                "off": 8,
                "pre": 35,
                "post": 100,
                "OFF": 8,
                "PRE": 35,
                "POST": 100,
                "0": 0
            }
            return settings.get(setting, get_random_macro_value())
        def dist_bw_to_percentage(input_value):
            input_value = float(input_value)
            if not isinstance(input_value, (int, float)):
                return get_random_macro_value()
            if input_value < 0.1:
                return 0
            elif input_value > 7.6:
                return 100
            # Piecewise interpolation based on provided mappings
            if 0.1 <= input_value <= 0.5:
                return round(10 + (input_value - 0.1) / (0.5 - 0.1) * (25 - 10), 1)
            elif 0.5 < input_value <= 1.9:
                return round(25 + (input_value - 0.5) / (1.9 - 0.5) * (50 - 25), 1)
            elif 1.9 < input_value <= 3.0:
                return round(50 + (input_value - 1.9) / (3.0 - 1.9) * (62 - 50), 1)
            elif 3.0 < input_value <= 3.6:
                return round(62 + (input_value - 3.0) / (3.6 - 3.0) * (68.9 - 62), 1)
            elif 3.6 < input_value <= 4.3:
                return round(68.9 + (input_value - 3.6) / (4.3 - 3.6) * (75 - 68.9), 1)
            elif 4.3 < input_value <= 7.6:
                return round(75 + (input_value - 4.3) / (7.6 - 4.3) * (100 - 75), 1)
            return get_random_macro_value()
        def phase_rate_to_macro(rate_str):
            try:
                rate = float(rate_str.replace(" Hz", ""))
            except ValueError:
                return get_random_macro_value()
            if rate < 0.0 or rate > 20.0:
                return get_random_macro_value()
            # Piecewise interpolation based on provided mappings
            if 0.0 <= rate <= 0.03:
                return round((rate / 0.03) * 20, 1)
            elif 0.03 < rate <= 0.16:
                return round(20 + (rate - 0.03) / (0.16 - 0.03) * (30 - 20), 1)
            elif 0.16 < rate <= 0.51:
                return round(30 + (rate - 0.16) / (0.51 - 0.16) * (40 - 30), 1)
            elif 0.51 < rate <= 1.25:
                return round(40 + (rate - 0.51) / (1.25 - 0.51) * (50 - 40), 1)
            elif 1.25 < rate <= 2.59:
                return round(50 + (rate - 1.25) / (2.59 - 1.25) * (60 - 50), 1)
            elif 2.59 < rate <= 4.80:
                return round(60 + (rate - 2.59) / (4.80 - 2.59) * (70 - 60), 1)
            elif 4.80 < rate <= 8.19:
                return round(70 + (rate - 4.80) / (8.19 - 4.80) * (80 - 70), 1)
            elif 8.19 < rate <= 13.12:
                return round(80 + (rate - 8.19) / (13.12 - 8.19) * (90 - 80), 1)
            elif 13.12 < rate <= 20.0:
                return round(90 + (rate - 13.12) / (20.0 - 13.12) * (100 - 90), 1)
            return get_random_macro_value()
        def degrees_to_percentage(deg_str):
            try:
                degrees = float(deg_str.replace("deg.", ""))
            except ValueError:
                degrees = float(deg_str)
            if degrees < 0 or degrees > 360:
                return get_random_macro_value()
            percentage = (degrees / 360) * 100
            return round(percentage, 1)
        def cho_dly_to_percentage(ms_str):
            try:
                ms_value = float(ms_str.replace(" ms", ""))
            except ValueError:
                return get_random_macro_value()
            if ms_value < 0.0 or ms_value > 20.0:
                return get_random_macro_value()
            # Piecewise interpolation based on provided mappings
            if 0.0 <= ms_value <= 0.2:
                return round((ms_value / 0.2) * 10, 1)
            elif 0.2 < ms_value <= 0.8:
                return round(10 + (ms_value - 0.2) / (0.8 - 0.2) * (20 - 10), 1)
            elif 0.8 < ms_value <= 1.8:
                return round(20 + (ms_value - 0.8) / (1.8 - 0.8) * (30 - 20), 1)
            elif 1.8 < ms_value <= 3.2:
                return round(30 + (ms_value - 1.8) / (3.2 - 1.8) * (40 - 30), 1)
            elif 3.2 < ms_value <= 5.0:
                return round(40 + (ms_value - 3.2) / (5.0 - 3.2) * (50 - 40), 1)
            elif 5.0 < ms_value <= 7.2:
                return round(50 + (ms_value - 5.0) / (7.2 - 5.0) * (60 - 50), 1)
            elif 7.2 < ms_value <= 9.8:
                return round(60 + (ms_value - 7.2) / (9.8 - 7.2) * (70 - 60), 1)
            elif 9.8 < ms_value <= 12.8:
                return round(70 + (ms_value - 9.8) / (12.8 - 9.8) * (80 - 70), 1)
            elif 12.8 < ms_value <= 16.2:
                return round(80 + (ms_value - 12.8) / (16.2 - 12.8) * (90 - 80), 1)
            elif 16.2 < ms_value <= 20.0:
                return round(90 + (ms_value - 16.2) / (20.0 - 16.2) * (100 - 90), 1)
            return get_random_macro_value()
        def cho_dep_to_percentage(ms_str):
            try:
                ms_value = float(ms_str.replace(" ms", ""))
            except ValueError:
                return float(ms_str)
            if ms_value < 0.0 or ms_value > 26.0:
                return get_random_macro_value()
            # Piecewise interpolation based on provided mappings
            if 0.0 <= ms_value <= 0.3:
                return round((ms_value / 0.3) * 10, 1)
            elif 0.3 < ms_value <= 1.0:
                return round(10 + (ms_value - 0.3) / (1.0 - 0.3) * (20 - 10), 1)
            elif 1.0 < ms_value <= 2.3:
                return round(20 + (ms_value - 1.0) / (2.3 - 1.0) * (30 - 20), 1)
            elif 2.3 < ms_value <= 4.2:
                return round(30 + (ms_value - 2.3) / (4.2 - 2.3) * (40 - 30), 1)
            elif 4.2 < ms_value <= 6.5:
                return round(40 + (ms_value - 4.2) / (6.5 - 4.2) * (50 - 40), 1)
            elif 6.5 < ms_value <= 9.4:
                return round(50 + (ms_value - 6.5) / (9.4 - 6.5) * (60 - 50), 1)
            elif 9.4 < ms_value <= 12.7:
                return round(60 + (ms_value - 9.4) / (12.7 - 9.4) * (70 - 60), 1)
            elif 12.7 < ms_value <= 16.6:
                return round(70 + (ms_value - 12.7) / (16.6 - 12.7) * (80 - 70), 1)
            elif 16.6 < ms_value <= 21.1:
                return round(80 + (ms_value - 16.6) / (21.1 - 16.6) * (90 - 80), 1)
            elif 21.1 < ms_value <= 26.0:
                return round(90 + (ms_value - 21.1) / (26.0 - 21.1) * (100 - 90), 1)
            return get_random_macro_value()
        def cho_filt_to_percentage(freq_str):
            try:
                freq = float(freq_str.replace(" Hz", ""))
            except ValueError:
                freq = float(freq_str)
            if freq < 50.0 or freq > 20000.0:
                return get_random_macro_value()
            # Piecewise interpolation based on provided mappings
            if 50 <= freq <= 91:
                return round((freq - 50) / (91 - 50) * 10, 1)
            elif 91 < freq <= 166:
                return round(10 + (freq - 91) / (166 - 91) * (20 - 10), 1)
            elif 166 < freq <= 302:
                return round(20 + (freq - 166) / (302 - 166) * (30 - 20), 1)
            elif 302 < freq <= 549:
                return round(30 + (freq - 302) / (549 - 302) * (40 - 30), 1)
            elif 549 < freq <= 1000:
                return round(40 + (freq - 549) / (1000 - 549) * (50 - 40), 1)
            elif 1000 < freq <= 1821:
                return round(50 + (freq - 1000) / (1821 - 1000) * (60 - 50), 1)
            elif 1821 < freq <= 3314:
                return round(60 + (freq - 1821) / (3314 - 1821) * (70 - 60), 1)
            elif 3314 < freq <= 6034:
                return round(70 + (freq - 3314) / (6034 - 3314) * (80 - 70), 1)
            elif 6034 < freq <= 10986:
                return round(80 + (freq - 6034) / (10986 - 6034) * (90 - 80), 1)
            elif 10986 < freq <= 20000:
                return round(90 + (freq - 10986) / (20000 - 10986) * (100 - 90), 1)
            return get_random_macro_value()
        def dist_freq_to_percentage(freq_str):
            try:
                freq = float(freq_str.replace(" Hz", ""))
            except ValueError:
                freq = float(freq_str)
            if freq < 8.0:
                return 0.0
            elif freq > 13290.0:
                return 100.0
            # Piecewise interpolation based on provided mappings
            if 8 <= freq <= 17:
                return round((freq - 8) / (17 - 8) * 10, 1)
            elif 17 < freq <= 36:
                return round(10 + (freq - 17) / (36 - 17) * (20 - 10), 1)
            elif 36 < freq <= 75:
                return round(20 + (freq - 36) / (75 - 36) * (30 - 20), 1)
            elif 75 < freq <= 157:
                return round(30 + (freq - 75) / (157 - 75) * (40 - 30), 1)
            elif 157 < freq <= 330:
                return round(40 + (freq - 157) / (330 - 157) * (50 - 40), 1)
            elif 330 < freq <= 690:
                return round(50 + (freq - 330) / (690 - 330) * (60 - 50), 1)
            elif 690 < freq <= 1446:
                return round(60 + (freq - 690) / (1446 - 690) * (70 - 60), 1)
            elif 1446 < freq <= 3030:
                return round(70 + (freq - 1446) / (3030 - 1446) * (80 - 70), 1)
            elif 3030 < freq <= 6346:
                return round(80 + (freq - 3030) / (6346 - 3030) * (90 - 80), 1)
            elif 6346 < freq <= 13290:
                return round(90 + (freq - 6346) / (13290 - 6346) * (100 - 90), 1)
            return get_random_macro_value()
        def dly_freq_to_percentage(freq_str):
            try:
                freq = float(freq_str.replace(" Hz", ""))
            except ValueError:
                freq = float(freq_str)
            if freq < 40.0:
                return 0.0
            elif freq > 18000.0:
                return 100.0
            # Piecewise interpolation based on provided mappings
            if 40 <= freq <= 74:
                return round((freq - 40) / (74 - 40) * 10, 1)
            elif 74 < freq <= 136:
                return round(10 + (freq - 74) / (136 - 74) * (20 - 10), 1)
            elif 136 < freq <= 250:
                return round(20 + (freq - 136) / (250 - 136) * (30 - 20), 1)
            elif 250 < freq <= 461:
                return round(30 + (freq - 250) / (461 - 250) * (40 - 30), 1)
            elif 461 < freq <= 849:
                return round(40 + (freq - 461) / (849 - 461) * (50 - 40), 1)
            elif 849 < freq <= 1563:
                return round(50 + (freq - 849) / (1563 - 849) * (60 - 50), 1)
            elif 1563 < freq <= 2879:
                return round(60 + (freq - 1563) / (2879 - 1563) * (70 - 60), 1)
            elif 2879 < freq <= 5304:
                return round(70 + (freq - 2879) / (5304 - 2879) * (80 - 70), 1)
            elif 5304 < freq <= 9771:
                return round(80 + (freq - 5304) / (9771 - 5304) * (90 - 80), 1)
            elif 9771 < freq <= 18000:
                return round(90 + (freq - 9771) / (18000 - 9771) * (100 - 90), 1)
            return get_random_macro_value()
        def phs_frq_to_percentage(freq_str):
            try:
                freq = float(freq_str.replace(" Hz", ""))
            except ValueError:
                freq = float(freq_str)
            if freq < 20.0:
                return 0.0
            elif freq > 18000.0:
                return 100.0
            # Piecewise interpolation based on provided mappings
            if 20 <= freq <= 39:
                return round((freq - 20) / (39 - 20) * 10, 1)
            elif 39 < freq <= 77:
                return round(10 + (freq - 39) / (77 - 39) * (20 - 10), 1)
            elif 77 < freq <= 153:
                return round(20 + (freq - 77) / (153 - 77) * (30 - 20), 1)
            elif 153 < freq <= 303:
                return round(30 + (freq - 153) / (303 - 153) * (40 - 30), 1)
            elif 303 < freq <= 600:
                return round(40 + (freq - 303) / (600 - 303) * (50 - 40), 1)
            elif 600 < freq <= 1184:
                return round(50 + (freq - 600) / (1184 - 600) * (60 - 50), 1)
            elif 1184 < freq <= 2338:
                return round(60 + (freq - 1184) / (2338 - 1184) * (70 - 60), 1)
            elif 2338 < freq <= 4617:
                return round(70 + (freq - 2338) / (4617 - 2338) * (80 - 70), 1)
            elif 4617 < freq <= 9116:
                return round(80 + (freq - 4617) / (9116 - 4617) * (90 - 80), 1)
            elif 9116 < freq <= 18000:
                return round(90 + (freq - 9116) / (18000 - 9116) * (100 - 90), 1)
            return get_random_macro_value()
        def EQfrq_to_percentage(freq_str):
            try:
                freq = float(freq_str.replace(" Hz", ""))
            except ValueError:
                freq = float(freq_str)
            if freq < 22.0:
                return 0.0
            elif freq > 20000.0:
                return 100.0
            # Piecewise interpolation based on provided mappings
            if 22 <= freq <= 43:
                return round((freq - 22) / (43 - 22) * 10, 1)
            elif 43 < freq <= 84:
                return round(10 + (freq - 43) / (84 - 43) * (20 - 10), 1)
            elif 84 < freq <= 167:
                return round(20 + (freq - 84) / (167 - 84) * (30 - 20), 1)
            elif 167 < freq <= 331:
                return round(30 + (freq - 167) / (331 - 167) * (40 - 30), 1)
            elif 331 < freq <= 656:
                return round(40 + (freq - 331) / (656 - 331) * (50 - 40), 1)
            elif 656 < freq <= 1300:
                return round(50 + (freq - 656) / (1300 - 656) * (60 - 50), 1)
            elif 1300 < freq <= 2574:
                return round(60 + (freq - 1300) / (2574 - 1300) * (70 - 60), 1)
            elif 2574 < freq <= 5099:
                return round(70 + (freq - 2574) / (5099 - 2574) * (80 - 70), 1)
            elif 5099 < freq <= 10098:
                return round(80 + (freq - 5099) / (10098 - 5099) * (90 - 80), 1)
            elif 10098 < freq <= 20000:
                return round(90 + (freq - 10098) / (20000 - 10098) * (100 - 90), 1)
            return get_random_macro_value()
        def dly_bw_to_percentage(value_str):
            try:
                value = float(value_str)
            except ValueError:
                return get_random_macro_value()
            if value < 0.8:
                return 0.0
            elif value > 8.2:
                return 100.0
            # Piecewise interpolation based on provided mappings
            if 0.8 <= value <= 1.5:
                return round((value - 0.8) / (1.5 - 0.8) * 10, 1)
            elif 1.5 < value <= 2.2:
                return round(10 + (value - 1.5) / (2.2 - 1.5) * (20 - 10), 1)
            elif 2.2 < value <= 3.0:
                return round(20 + (value - 2.2) / (3.0 - 2.2) * (30 - 20), 1)
            elif 3.0 < value <= 3.8:
                return round(30 + (value - 3.0) / (3.8 - 3.0) * (40 - 30), 1)
            elif 3.8 < value <= 4.5:
                return round(40 + (value - 3.8) / (4.5 - 3.8) * (50 - 40), 1)
            elif 4.5 < value <= 5.3:
                return round(50 + (value - 4.5) / (5.3 - 4.5) * (60 - 50), 1)
            elif 5.3 < value <= 6.0:
                return round(60 + (value - 5.3) / (6.0 - 5.3) * (70 - 60), 1)
            elif 6.0 < value <= 6.8:
                return round(70 + (value - 6.0) / (6.8 - 6.0) * (80 - 70), 1)
            elif 6.8 < value <= 7.5:
                return round(80 + (value - 6.8) / (7.5 - 6.8) * (90 - 80), 1)
            elif 7.5 < value <= 8.2:
                return round(90 + (value - 7.5) / (8.2 - 7.5) * (100 - 90), 1)
            return get_random_macro_value()
        def cmp_thr_to_percentage(threshold_str):
            try:
                threshold = float(threshold_str.replace(" dB", ""))
            except ValueError:
                return get_random_macro_value()
            if threshold > 0.0:
                return 0.0
            elif threshold < -120.0:
                return 100.0
            # Piecewise interpolation based on provided mappings
            if -120.0 <= threshold <= -60.0:
                return round(90 + (threshold + 60) / (-120 + 60) * (100 - 90), 1)
            elif -60.0 < threshold <= -41.9:
                return round(80 + (threshold + 41.9) / (-60 + 41.9) * (90 - 80), 1)
            elif -41.9 < threshold <= -31.4:
                return round(70 + (threshold + 31.4) / (-41.9 + 31.4) * (80 - 70), 1)
            elif -31.4 < threshold <= -23.9:
                return round(60 + (threshold + 23.9) / (-31.4 + 23.9) * (70 - 60), 1)
            elif -23.9 < threshold <= -18.1:
                return round(50 + (threshold + 18.1) / (-23.9 + 18.1) * (60 - 50), 1)
            elif -18.1 < threshold <= -13.3:
                return round(40 + (threshold + 13.3) / (-18.1 + 13.3) * (50 - 40), 1)
            elif -13.3 < threshold <= -9.3:
                return round(30 + (threshold + 9.3) / (-13.3 + 9.3) * (40 - 30), 1)
            elif -9.3 < threshold <= -5.8:
                return round(20 + (threshold + 5.8) / (-9.3 + 5.8) * (30 - 20), 1)
            elif -5.8 < threshold <= -2.7:
                return round(10 + (threshold + 2.7) / (-5.8 + 2.7) * (20 - 10), 1)
            elif -2.7 < threshold <= 0.0:
                return round((threshold / -2.7) * 10, 1)
            return get_random_macro_value()
        def cmp_att_to_percentage(attack_str):
            try:
                attack_time = float(attack_str.replace(" ms", ""))
            except ValueError:
                return get_random_macro_value()
            if attack_time < 0.1:
                return 0.0
            elif attack_time > 1000.0:
                return 100.0
            # Piecewise interpolation based on provided mappings
            if 0.1 <= attack_time <= 10.1:
                return round((attack_time - 0.1) / (10.1 - 0.1) * 10, 1)
            elif 10.1 < attack_time <= 40.1:
                return round(10 + (attack_time - 10.1) / (40.1 - 10.1) * (20 - 10), 1)
            elif 40.1 < attack_time <= 90.1:
                return round(20 + (attack_time - 40.1) / (90.1 - 40.1) * (30 - 20), 1)
            elif 90.1 < attack_time <= 160.1:
                return round(30 + (attack_time - 90.1) / (160.1 - 90.1) * (40 - 30), 1)
            elif 160.1 < attack_time <= 250.1:
                return round(40 + (attack_time - 160.1) / (250.1 - 160.1) * (50 - 40), 1)
            elif 250.1 < attack_time <= 360.1:
                return round(50 + (attack_time - 250.1) / (360.1 - 250.1) * (60 - 50), 1)
            elif 360.1 < attack_time <= 490.1:
                return round(60 + (attack_time - 360.1) / (490.1 - 360.1) * (70 - 60), 1)
            elif 490.1 < attack_time <= 640.0:
                return round(70 + (attack_time - 490.1) / (640.0 - 490.1) * (80 - 70), 1)
            elif 640.0 < attack_time <= 810.0:
                return round(80 + (attack_time - 640.0) / (810.0 - 640.0) * (90 - 80), 1)
            elif 810.0 < attack_time <= 1000.0:
                return round(90 + (attack_time - 810.0) / (1000.0 - 810.0) * (100 - 90), 1)
            return get_random_macro_value()
        def cmpgain_to_percentage(gain_str):
            try:
                gain = float(gain_str.replace(" dB", ""))
            except ValueError:
                return get_random_macro_value()
            if gain < 0.0:
                return 0.0
            elif gain > 30.1:
                return 100.0
            # Piecewise interpolation based on provided mappings
            if 0.0 <= gain <= 2.3:
                return round((gain / 2.3) * 10, 1)
            elif 2.3 < gain <= 7.0:
                return round(10 + (gain - 2.3) / (7.0 - 2.3) * (20 - 10), 1)
            elif 7.0 < gain <= 11.6:
                return round(20 + (gain - 7.0) / (11.6 - 7.0) * (30 - 20), 1)
            elif 11.6 < gain <= 15.5:
                return round(30 + (gain - 11.6) / (15.5 - 11.6) * (40 - 30), 1)
            elif 15.5 < gain <= 18.8:
                return round(40 + (gain - 15.5) / (18.8 - 15.5) * (50 - 40), 1)
            elif 18.8 < gain <= 21.7:
                return round(50 + (gain - 18.8) / (21.7 - 18.8) * (60 - 50), 1)
            elif 21.7 < gain <= 24.7:
                return round(60 + (gain - 21.7) / (24.7 - 21.7) * (70 - 60), 1)
            elif 24.7 < gain <= 26.4:
                return round(70 + (gain - 24.7) / (26.4 - 24.7) * (80 - 70), 1)
            elif 26.4 < gain <= 28.3:
                return round(80 + (gain - 26.4) / (28.3 - 26.4) * (90 - 80), 1)
            elif 28.3 < gain <= 30.1:
                return round(90 + (gain - 28.3) / (30.1 - 28.3) * (100 - 90), 1)
            # Fallback in case of an unexpected value
            return get_random_macro_value()
        def eq_vol_to_percentage(gain_str):
            try:
                gain = float(gain_str.replace(" dB", ""))
            except ValueError:
                return get_random_macro_value()
            if gain < -24.0:
                return 0.0
            elif gain > 24.0:
                return 100.0
            percentage = ((gain + 24) / 48) * 100
            return round(percentage, 1)
        def dly_mode_to_percentage(mode):
            if mode == "Normal" or mode == "0":
                return 18
            if mode == "Ping-Pong" or mode == "ping pong" or mode == "pingpong" or mode == "PingPong" or mode == "Ping Pong" or mode == "1":
                return 30
            if mode == "Tap->Delay" or mode == "2" or mode == "tapdelay" or mode == "TapDelay" or mode == "tap delay" or mode == "Tap Delay" or mode == "2":
                return 80
            return get_random_macro_value()
        def eqTyp_to_percentage(mode):
            if mode == "Shelf" or mode == "shelf" or mode == "0":
                return 18
            if mode == "peak" or mode == "Peak" or mode == "PEAK" or mode == "1":
                return 30
            if mode == "LPF" or mode == "LP" or mode == "lpf" or mode == "lowpass" or mode == "Lpf" or mode == "2":
                return 80
            return get_random_macro_value()
        def delay_time_to_percentage(input_str):
            if "ms" in input_str or input_str.replace('.', '', 1).isdigit():
                try:
                    delay_time = float(input_str.replace(" ms", ""))
                except ValueError:
                    return get_random_macro_value()
                if delay_time < 1.0:
                    return 0.0
                elif delay_time > 501.0:
                    return 100.0
                # Piecewise interpolation for ms values
                if 1.0 <= delay_time <= 1.05:
                    return round((delay_time - 1.0) / (1.05 - 1.0) * 10, 1)
                elif 1.05 < delay_time <= 1.8:
                    return round(10 + (delay_time - 1.05) / (1.8 - 1.05) * (20 - 10), 1)
                elif 1.8 < delay_time <= 5.05:
                    return round(20 + (delay_time - 1.8) / (5.05 - 1.8) * (30 - 20), 1)
                elif 5.05 < delay_time <= 13.8:
                    return round(30 + (delay_time - 5.05) / (13.8 - 5.05) * (40 - 30), 1)
                elif 13.8 < delay_time <= 32.25:
                    return round(40 + (delay_time - 13.8) / (32.25 - 13.8) * (50 - 40), 1)
                elif 32.25 < delay_time <= 65.8:
                    return round(50 + (delay_time - 32.25) / (65.8 - 32.25) * (60 - 50), 1)
                elif 65.8 < delay_time <= 121.05:
                    return round(60 + (delay_time - 65.8) / (121.05 - 65.8) * (70 - 60), 1)
                elif 121.05 < delay_time <= 205.8:
                    return round(70 + (delay_time - 121.05) / (205.8 - 121.05) * (80 - 70), 1)
                elif 205.8 < delay_time <= 329.05:
                    return round(80 + (delay_time - 205.8) / (329.05 - 205.8) * (90 - 80), 1)
                elif 329.05 < delay_time <= 501.0:
                    return round(90 + (delay_time - 329.05) / (501.0 - 329.05) * (100 - 90), 1)
            else:
                beat_mappings = {
                    "fast": 0.0,
                    "1/256": 7.09,
                    "1/128": 19.7,
                    "1/64": 25.2,
                    "1/32": 34.6,
                    "1/16": 48.0,
                    "1/8": 55.1,
                    "1/4": 60.6,
                    "1/2": 76.4,
                    "Bar": 78.0,
                    "2 Bar": 89.0,
                    "4 Bar": 100.0
                }
                if input_str in beat_mappings:
                    return beat_mappings[input_str]
                else:
                    return get_random_macro_value()
            return get_random_macro_value()

        def normalize_for_midi(name, value):
            value_parse = [name, value]
            # return get_random_macro_value()
            # print(value_parse[0])
            try:
                if value_parse[0] == "Env1 Atk" or value_parse[0] == "Env1 Hold" or value_parse[0] == "Env1 Dec" or \
                        value_parse[0] == "Env1 Rel":
                    return normalize_ms_s(value)
                elif value_parse[0] == "Env1 Sus":
                    return normalize_dB_to_midi(value)
                elif value_parse[0] == "A Pan" or value_parse[0] == "B Pan":
                    return normalize_pan_to_midi(value)
                elif value_parse[0] == "Cho_Dep":
                    return cho_depth_to_percentage(value)
                elif value_parse[0] == "B WTPos":
                    return wt_to_macro(value)
                elif value_parse[0] == "A WTPos":
                    return wt_to_midi(value)
                elif value_parse[0] == "A Vol":
                    return percentage_to_midi(value)
                elif value_parse[0] == "Noise Level" or value_parse[0] == "B Vol" or value_parse[0] == "Sub Osc Level":
                    return percentage_to_macro(value)
                elif value_parse[0] == "Cho_Feed":
                    return cho_feed_to_macro(value)
                elif "%" in value_parse[1] and "(" not in value_parse[1]:
                    return percentage_to_macro(value)
                elif value_parse[0] == "B Unison":
                    return unison_to_macro(value)
                elif value_parse[0] == "A Unison":
                    return unison_to_midi(value)
                elif value_parse[0] == "A Octave":
                    return oct_to_midi(value)
                elif value_parse[0] == "A Semi" or value_parse[0] == "B Semi":
                    return semi_to_macro(value)
                elif value_parse[0] == "A Fine" or value_parse[0] == "B Fine":
                    return fine_to_macro(value)
                elif value_parse[0] == "Fil Cutoff":
                    return frequency_to_percentage(value)
                elif value_parse[0] == "Fil Type" or value_parse[0] == "FX Fil Type":
                    return filter_type_to_macro(value)
                elif value_parse[0] == "Dist_Mode":
                    return distortion_type_to_macro(value)
                elif value_parse[0] == "A UniBlend" or value_parse[0] == "B UniBlend" or value_parse[0] == "Comp_Wet":
                    return value
                elif value_parse[0] == "SubOscShape":
                    return sub_shape_to_macro(value)
                elif value_parse[0] == "B Octave" or value_parse[0] == "SubOscOctave":
                    return oct_to_macro(value)
                elif value_parse[0] == "Hyp_Retrig":
                    return on_to_percentage(value)
                elif value_parse[0] == "Hyp_Unison":
                    return hyp_unison_to_macro(value)
                elif value_parse[0] == "A UniDet" or value_parse[0] == "B UniDet":
                    return uni_det_to_macro(value)
                elif value_parse[0] == "Dist_PrePost":
                    return dist_pre_post_to_macro(value)
                elif value_parse[0] == "Dist_BW":
                    return dist_bw_to_percentage(value)
                elif value_parse[0] == "Cho_Rate" or value_parse[0] == "Phs_Rate" or value_parse[0] == "Flg_Rate":
                    return phase_rate_to_macro(value)
                elif value_parse[0] == "Flg_Stereo" or value_parse[0] == "Phs_Stereo":
                    return degrees_to_percentage(value)
                elif value_parse[0] == "Cho_Dly" or value_parse[0] == "Cho_Dly2":
                    return cho_dly_to_percentage(value)
                elif value_parse[0] == "Cho_Dep":
                    return cho_dep_to_percentage(value)
                elif value_parse[0] == "Cho_Filt":
                    return cho_filt_to_percentage(value)
                elif value_parse[0] == "Dist_Freq":
                    return dist_freq_to_percentage(value)
                elif value_parse[0] == "Dly_Freq":
                    return dly_freq_to_percentage(value)
                elif value_parse[0] == "Phs_Frq":
                    return phs_frq_to_percentage(value)
                elif value_parse[0] == "EQ FrqL" or value_parse[0] == "EQ FrqH":
                    return EQfrq_to_percentage(value)
                elif value_parse[0] == "FX Fil Freq":
                    return dist_freq_to_percentage(value)
                elif value_parse[0] == "Dly_Link":
                    return on_to_percentage(value)
                elif value_parse[0] == "Dly_TimL" or value_parse[0] == "DlyTimR":
                    return delay_time_to_percentage(value)
                elif value_parse[0] == "Dly_BW":
                    return dly_bw_to_percentage(value)
                elif value_parse[0] == "Dly_Mode":
                    return dly_mode_to_percentage(value)
                elif value_parse[0] == "Cmp_Thr":
                    return cmp_thr_to_percentage(value)
                elif value_parse[0] == "Cmp_Att":
                    return cmp_att_to_percentage(value)
                elif value_parse[0] == "Cmp_Rel":
                    return cmp_att_to_percentage(value)
                elif value_parse[0] == "CmpGain":
                    return cmpgain_to_percentage(value)
                elif value_parse[0] == "CmpMBnd":
                    return CmpMBnd_to_percentage(value)
                elif value_parse[0] == "EQ VolL" or value_parse[0] == "EQ VolH":
                    return eq_vol_to_percentage(value)
                elif value_parse[0] == "EQ TypL" or value_parse[0] == "EQ TypH":
                    return eqTyp_to_percentage(value)
                elif value_parse[1] == "on" or value_parse[1] == "off":
                    return on_to_percentage(value)
            except:
                print("error", value_parse)
                return get_random_midi_value()

        port_dictionary = {"Env1 Atk": {"Port": 8000, "Value": 0},
                           "Env1 Hold": {"Port": 8001, "Value": 0}, "Env1 Dec": {"Port": 8002, "Value": 0}}
        #Showing first three to give a sense as to how we will parse through each parameter
        current_port = 8000
        for (name, value) in final_parameter_list:
            port_dictionary[name] = {"Port": current_port, "Value": normalize_for_midi(name, value)}
            current_port += 1
        for key in port_dictionary:
            send_osc(port_dictionary[key]["Port"], port_dictionary[key]["Value"])
        print("Applied to Serum")

dispatcher = dispatcher.Dispatcher()
dispatcher.map("/user_prompt", message_handler)
ip = "127.0.0.1"
port = 9000
server = osc_server.ThreadingOSCUDPServer((ip, port), dispatcher)
print("Listening for OSC messages on", ip, ":", port)
server.serve_forever()




