# Oximeter GUI

## Description

This is a Python GUI for a BLE oximeter. It connects to the oximeter, reads data, and displays it in a user-friendly interface.
Reverse engineering was done with the help of OpenAI's ChatGPT, which provided code snippets and guidance throughout the process.

## Backstory

One evening, I opened a drawer and spotted a no-name oximeter with BLE capabilities that I'd purchased on AliExpress—without any BLE software.
After reading OpenAI's article about their new models, I thought: "Let me try..."
I asked: "Hey, I have a no-name oximeter. Here's the BLE scan result—can you write Python code to read it?"
The AI wrote a guide on reverse engineering (familiar territory) and provided an example of an oximeter similar to mine that used the same vendor-specific service.
After several attempts, it produced a program that captured a data stream, but the "PI, PPG, PPG2, BPM, SpO2" values were completely wrong.
After a few more exchanges, the AI seemed stuck in an endless loop trying to decode the data.
- "Can you just dump the raw data for me?" I asked.
The AI wrote code to dump the raw data, and I discovered 4 bytes that resembled SpO2 and BPM values.
- "At this offset, this data looks like SpO2 and BPM. Can you decode it using this knowledge?"
The AI wrote code that successfully decoded it, referencing something it had seen online, and even extracted the PI value. Impressive!
I ask it more - "There are also 5 chunks of some data—what might they be? Perhaps a waveform?"
The AI analyzed this and displayed a pulse waveform!
- "Can you write me a nice GUI to show all this data?"
Success.

