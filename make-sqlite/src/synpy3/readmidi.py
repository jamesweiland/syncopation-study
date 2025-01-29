# -*- coding: utf-8 -*-
"""
Created on Sat Mar 21 22:19:52 2015

@author: christopherh
"""

#from RhythmParser import Bar

from music_objects import *
from basic_functions import *

from miditoolkit import MidiFile
import miditoolkit

def overloaded_lt(l: miditoolkit.Note, r: miditoolkit.Note) -> bool:
	""" overloading the < operator in miditoolkit's Note object so sort() can be called on it """
	return l.start < r.start

miditoolkit.Note.__lt__ = overloaded_lt

def read_midi_file(filename):
	""" open and read a MIDI file, return a MidiFile object """
	return MidiFile(filename)

# def get_bars(midiFile, trackindex=1):
# 	""" returns a list of bar objects from a MidiFile object """

# 	# select a track to extract (default = 1, ignoring dummy track 0)
# 	track = midiFile.tracks[trackindex] 
# 	eventIndex = 0
# 	numNotes = 0

# 	noteonlist = []
# 	noteOnFound==True

# 	while noteOnFound==True:
# 		(noteOnIndex, noteOnDelta, noteOnFound) = self.find_event(track, eventIndex, lambda e: e.type == 'NOTE_ON')
# 		noteEvent = track.events[noteOnIndex]
# 		eventIndex = noteOnIndex + 1
            	

#find_event(x.tracks[0], 0, lambda e: (e.type == 'NOTE_ON') | (e.type == 'KEY_SIGNATURE') | (e.type == "TIME_SIGNATURE"))

'''
	#read midiFile
	
	

	run through selected track getting notes out to build bars

'''
	


def get_bars_from_midi(midiFile: MidiFile):

	# couple of inner functions to tidy up getting the initial values of
	# tempo and time signature
	


	def get_time_signature(midiFile: MidiFile, barStartTime: float):
		
		timesigs = midiFile.time_signature_changes
		for i in range(len(timesigs)):
			if barStartTime < timesigs[i].time:
				break
		
		if i != len(timesigs) - 1:
			i -= 1

		return TimeSignature.from_mtk_timesig(timesigs[i]),calculate_bar_ticks(timesigs[i].numerator, timesigs[i].denominator, midiFile.ticks_per_beat)	

	def get_tempo(midiFile: MidiFile, barStartTime: float):
		
		tempo = None
		i=0
		tempos = midiFile.tempo_changes
		for i in range(len(tempos)):
			if barStartTime < tempos[i].time:
				break

		if i != len(tempos) - 1:
			i -= 1

		return tempos[i]




	# get notes from the midi file (absolute start times from start of file)
	notesList = []
	for instrument in midiFile.instruments:
		for note in instrument.notes:
			notesList.append(note)
	notesList.sort()
	

	# get initial tempo and time signature from time list
	timesig = midiFile.time_signature_changes[0]
	tempo = midiFile.tempo_changes[0]




	# ticks per quarter note:
	ticksPerQuarter = midiFile.ticks_per_beat
	#calculate the initial length of a bar in ticks
	barlength = calculate_bar_ticks(timesig.numerator, timesig.denominator, ticksPerQuarter)
	# initialise time for start and end of current bar
	barStartTime = 0
	barEndTime = 0# barlength
	

	# initialise bars list
	bars = BarList()
	noteIndex = 0

	note = notesList[0]
	# run through the notes list, chopping it into bars
	while noteIndex<len(notesList):
		#create a local note sequence to build a bar
		currentNotes = NoteSequence()

		[timesig,barlength] = get_time_signature(midiFile=midiFile, barStartTime=barStartTime)
		
		barEndTime = barEndTime + barlength

		tempo = get_tempo(midiFile=midiFile, barStartTime=barStartTime)
		

		#find all the notes in the current bar
		while(note.start < barEndTime):
			#make note start time relative to current bar
			note.start = note.start - barStartTime
			#add note to current bar note sequence
			currentNotes.append(note)
			noteIndex = noteIndex + 1
			if noteIndex<len(notesList):
				note = notesList[noteIndex]
			else:
				break

		# create a new bar from the current notes and add it to the list of bars
		bars.append(Bar(currentNotes, timesig, ticksPerQuarter, tempo))

		barStartTime = barEndTime

	return bars




