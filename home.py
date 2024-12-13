import streamlit as st
import librosa
#midi export is from https://stackoverflow.com/questions/11059801/how-can-i-write-a-midi-file-with-python 9/28/2024
from midiutil.MidiFile import MIDIFile
from midi2audio import FluidSynth
#NOTE: Use streamlit run -filename- to execute the program
#when testing, Ctrl+C the terminal before exiting the tab or else the terminal freezes.
st.title("Music Stenography")

#declare globals
if "out_text" not in st.session_state:
    st.session_state.out_text = ""
if "in_text" not in st.session_state:
    st.session_state.in_text = ""
if "first_time" not in st.session_state:#make sure not to process nothing
    st.session_state.first_time = True
if "uploader" not in st.session_state:
    st.session_state.uploader = None
outFile = None
#quickly write an empty outFile
mf = MIDIFile(1)     # 1 track
mf.addTrackName(0, 0, "output")#add trackname at track 0 time 0
mf.addTempo(0, 0, 120)#add tempo at track 0 time 0. Tempo variable was created earlier
# write it to disk
with open("output.mid", 'wb') as outf:
    mf.writeFile(outf)
outFile = open("output.mid", 'rb')
with open("musicStenographySave.mssf", 'w+') as file:
    file.write("")
stenoSave = open("musicStenographySave.mssf", 'r')
#make the base wav file to make sure no errors occur trying to read it before created
fs = FluidSynth()#here, soundfonts can be specified.
fs.midi_to_audio('output.mid', 'output.wav')#should, at this point, be empty.
def parse_note(instringunfiltered):#turns one note into a parsed note. The returned note is: [notelength in beats, midinotevalue, midinotevalue] (midinotevalue being the midi id number for that note)
    instring = instringunfiltered.lower()#make sure no capitals mess it up.
    notelength = 0
    if 'w' in instring:#identify length, remove identifier
        notelength = 4
        instring = instring.replace('w', '')
    if 'h' in instring:
        notelength = 2
        instring =instring.replace('h', '')
    if 'q' in instring:
        notelength = 1
        instring =instring.replace('q', '')
    if 'i' in instring:
        notelength = 0.5
        instring =instring.replace('i', '')
    if 's' in instring:
        notelength = 0.25
        instring =instring.replace('s', '')
    if 't' in instring:
        notelength = 0.125
        instring =instring.replace('t', '')
    if '.' in instring:
        notelength *= 1.5
        instring =instring.replace('.', '')
    #make sure it isn't a rest, and if it is, process that.
    if 'r' in instring:
        return [notelength]#that's all that is needed to identify the rest.
    #notelength has now been processed.
    eachnote = instring.split(' ')
    #process each midi note
    midinotes = []
    for item in eachnote:
        if item != "":#ignore empty notes
            noteprocessed = item.replace('-', '♭')
            midinotes.append(librosa.note_to_midi(noteprocessed))
    midinotes.insert(0, notelength)#put the notelength in the front of the list
    return midinotes
def process_repeats(instring):
    #The repeats are how many times it is played, not how many times it is repeated.
    #repeats cannot be called back to the start without a repeat start symbol there (<)
    #repeats without numbers assume to play the section twice
    split = list(instring)
    final = ""#the string that will be returned
    repeat_string = ""#what is to be repeated
    index = 0#for finding repeat numbers
    for character in split:
        if len(repeat_string) == 0:
            if character == "<":
                repeat_string += "<"
            else:
                final += character
        else:
            repeat_string = repeat_string.replace("<\n", "")#make sure we get rid of that identifying first character (it is there just to let the program know that a repeat has been started)
            if character == ">":
                #check to see if we find numbers before the next linebreak
                cur = index
                has_num = False
                digits = ""#we could have multiple-digit numbers
                while True:
                    if cur >= len(split):
                        break
                    if split[cur] == "\n":
                        break
                    if split[cur].isdigit():
                        digits += split[cur]
                        has_num = True
                    cur += 1
                number_repeats = 2#default is play it two times
                if has_num:
                    number_repeats = int(digits)
                for i in range(number_repeats):
                    if i == number_repeats -1:
                        #the following line removes a linebreak that should not be there. This is because we're not counting the ">", and the previous line had a linebreak.
                        repeat_string = repeat_string[:len(repeat_string)-1]
                    final += repeat_string
                repeat_string = ""
                for i in range(len(digits)+1):#remove the digits that show how many repeats
                    split.pop(index)
            else:
                repeat_string += character
        index += 1
    return final
def process_steno(text_in):
    outputtednotes = []
    text = process_repeats(text_in)
    splitinput = text.splitlines()
    errors = ""#to show the user any errors that could arise
    try:
        tempo = int(splitinput[0])
    except:
        return "Tempo data missing"
    splitinput.pop(0)
    line = 2
    for item in splitinput:
        try:
            outputtednotes.append(parse_note(item))
        except:
            errors += "Note syntax invalid on line"+str(line)+"  "#we can skip over the note with invalid data
        line += 1
    #then, we need to calculate the time of each note
    currenttime = 0
    for item in outputtednotes:
        item.insert(0, currenttime)
        currenttime += item[1]#make sure we are up to date on time
    return [tempo, outputtednotes, errors]
def on_userinput_update():#if we need to change the display data because the input has been updated
    if not st.session_state.first_time:
        try:
            fully_processed_data = process_steno(st.session_state.in_text)
            #process the fully_processed_data into usable text outputted to the user
            readable = "Tempo: "+str(fully_processed_data[0])+"\n"
            for chord in fully_processed_data[1]:
                #start time is not important, ignore
                if len(chord) > 2:
                    this_note = "Note lasting "+str(chord[1])+" beats with "
                    for i in range(len(chord)-2):
                        this_pitch = librosa.midi_to_note(chord[i+2])
                        this_note += this_pitch
                        this_note += ", "
                    readable += this_note
                    readable += "\n"
            readable += "Errors: "
            if len(fully_processed_data[2]) == 0:
                readable += "None"
            else:
                #for item in fully_processed_data[2]:
                #    readable += item
                #    readable += ", "
                readable += "".join(fully_processed_data[2])#this removes the comma separation problem.
            st.session_state.out_text = readable
            #now write the midi
            tempo = fully_processed_data[0]
            # create MIDI object
            mf = MIDIFile(1)     # 1 track
            mf.addTrackName(0, 0, "output")#add trackname at track 0 time 0
            mf.addTempo(0, 0, tempo)#add tempo at track 0 time 0. Tempo variable was created earlier
            #write each note we have
            for item in fully_processed_data[1]:
                time = item[0]
                duration = item[1]
                if len(item) > 2:#make sure this isn't intended to be a rest
                    for i in range(len(item)-2):#put each pitch into the midi
                        #mf.addNote(track, channel, pitch, time, duration, volume)
                        mf.addNote(0, 0, item[i+2], time, duration, 100)
            # write it to disk
            with open("output.mid", 'wb') as outf:
                mf.writeFile(outf)
            outFile = open("output.mid", 'rb')
            #write the shorthand file version to the disk
            with open("musicStenographySave.mssf", 'w+') as file:
                file.write(st.session_state.in_text)
            stenoSave = open('musicStenographySave.mssf', 'r')
            #make the wav file for playback
            fs.midi_to_audio('output.mid', 'output.wav')
        except Exception as e:
            st.session_state.out_text = "Tempo input error"
    else:
        st.session_state.first_time = False
from io import StringIO
def processShorthand():#upload a previous music shorthand save file (mssf)
    if st.session_state.upload_file != None:
        strung = StringIO(st.session_state.upload_file.getvalue().decode("utf-8")).read()
        st.session_state.in_text = strung
        st.session_state.first_time = False
#other global variables
steno_input = st.text_area("Input musical shorthand below: (Click off of input to process)", on_change = on_userinput_update(), key = "in_text")
steno_data_display = st.text(st.session_state.out_text)
previewPlayer = st.audio(open('output.wav', 'rb').read(), "audio/wav")#this is up here because it is more convenient to click
fully_processed_data = []#the note data outputted by the composer stenography program itself
download = st.download_button("Click to download MIDI", data=outFile, file_name = "output.mid")
downloadShorthand = st.download_button("Click to download musical shorthand file (to save this work for later)", data=stenoSave, file_name = "musicStenographySave.mssf")
uploadShorthand = st.file_uploader("Click to upload a previous musical shorthand file (.mssf)", on_change = processShorthand, key = "upload_file", type = ['mssf'])