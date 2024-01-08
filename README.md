# From-Above-Counting
Project Overview:

This project focuses on counting the number of people entering or leaving a building through multiple gates. It employs cameras positioned above each gate, using OpenCV, tracking, and motion detection algorithms. The system generates an Excel file for administrators to monitor and analyze the flow of people, aiding in statistical insights about the building's occupancy.
Usage:

    Modifying "main.py":
        To tailor the program to your needs, modify the "main.py" code by specifying gate names, URLs, and setting up parameters for each gate.

    Setting Up Requirements:
        Run pip install -r requirements.txt to install the necessary dependencies.

    Running the Program:
        Execute main.py after setup to initiate the counting process.
        Ensure there is a video stream available for the program to run on.

Program Architecture:

    Camera Setup:
        Camera URLs are configured, and each one is opened on a separate process to compensate for potential delays in camera reading.

    Gate Object Initialization:
        For each camera, a gate object is created with specific parameters (e.g., gate name, URL, tracking settings, etc.).
        A list of processes is established to run each gate on a separate process.

    Excel Handler Setup:
        An Excel handler is set up to write to the Excel file with a pre-defined format.

    Gate Process Workflow:
        Each gate process reads camera frames, initializes the tracker if necessary based on motion detection, and counts movements in either direction.
        Results are then written to the Excel file.

Customization and Tuning:

    Gate Parameters:
        Fine-tune parameters such as maxDisappeared, maxDistance, minNeighbor, etc., in the gate object based on your preferences.
