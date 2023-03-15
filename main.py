import time
from datetime import datetime
from gate import Gate
from excel_handler import excel
from multiprocessing import Process, Queue
from multiprocessing.shared_memory import ShareableList, SharedMemory

def gate_func(ex_loop, gate_name, url, maxDisappeared=1, maxDistance=125,
          minNeighbor=120, minStartEndPos=100, min_person_area=1400,
          frame_res=[640, 480], low_end_thres=40, dilate_iter=1, erode_iter=18,
          max_wait_cycles=720000, wait_seconds=1/200, wait_diplay_frame=1, maxage=10, gate_ID=0):

    gate = Gate(gate_name, url, maxDisappeared, maxDistance,
                minNeighbor, minStartEndPos, min_person_area,
                frame_res, low_end_thres, dilate_iter, erode_iter,max_wait_cycles,
                wait_seconds, wait_diplay_frame, maxage)
    start_day = datetime.now().strftime("%d")
          
    while ex_loop.buf[0]:
        gate.update()
        res = gate.read_result()
        up_down[gate_ID * 2] = res['Ups']
        up_down[gate_ID * 2 + 1] = res['Downs']

        if res['Status']:
            line = [datetime.now().strftime("%y:%m:%d"), datetime.now().strftime("%H:%M:%S"),
                    res['Ups'], res['Downs'], res['Ups'] - res['Downs']]
            queue_to_xl.put([gate.gate_name, line])
        gate.display_video(disp_differ=False,
                            disp_thres=False,
                            disp_main_frame=True)
        if datetime.now().strftime("%d") != start_day:
            start_time = datetime.now()strftime("%d")
            gate.ct.UPS = 0
            gate.ct.DOWNS = 0
    gate.close()

def excel_func(ex_loop):
    gate_format = ['Data', 'Time', 'Enters', 'Exists', 'inside']
    xl = excel('Electrical Department')
    last_hour = datetime.now()
    for gtname in gate_names:
        xl.add_sheet(gtname, gate_format)

    while ex_loop.buf[0]:
        try:
            gname, line = queue_to_xl.get(timeout=2)
        except:
            continue
        xl.append_to_sheet(gname, line)
        if datetime.now().strftime("%H") != last_hour:
            last_hour = datetime.now().strftime("%H")
            line = [datetime.now().strftime("%y:%m:%d"), datetime.now().strftime("%H:%M:%S")]
            tot_ups = 0
            tot_downs = 0
            for i in range(5):
                tot_ups += up_down[2 * i]
                tot_downs += up_down[2 * i + 1]
            line.append(tot_ups)
            line.append(tot_downs)
            line.append(tot_ups - tot_downs)
            xl.append_to_sheet('Main', line)
    xl.close()

if __name__ == '__main__':
    start_time = time.time()
    gate_names = ['Main Gate', 'Estraha Gate', 'Omara Gate', 'Perp Gate','Lab Gate']
    
    #urls = ['http://192.168.1.1:8080/?action=stream',
    #        'http://192.168.3.1:8080/?action=stream',
    #        'http://192.168.2.1:8080/?action=stream',
    #        'http://192.168.4.1:8080/?action=stream',
    #        'http://192.168.5.1:8080/?action=stream']

    urls = ['../Test_Vedio/Project_Elec.mp4',
            '../Test_Vedio/WhatsApp Video 2023-02-07 at 7.39.04 PM.mp4',
            '../Test_Vedio/WhatsApp Video 2023-02-07 at 7.39.52 PM.mp4',
            '../Test_Vedio/WhatsApp Video 2023-02-07 at 7.50.48 PM.mp4',
            '../Test_Vedio/WhatsApp Video 2023-02-08 at 4.06.33 PM.mp4']

    f = 1
    wc = 360000  # total waiting time = wc/f
    up_down = ShareableList([0 for _ in range(10)])

    """
    gate_name, url, maxDisappeared, maxDistance, minNeighbor, minStartEndPos, min_person_area,
    frame_res, low_end_thres, dilate_iter, erode_iter, max_wait_cycles, wait_seconds, wait_diplay_frame, maxage, gate_ID
    """

    g1 = (gate_names[0], urls[0], 3, 120, 100, 20, 50,
          [320, 240], 35, 4, 20, wc, 1/f, 1, 30, 0)

    g2 = (gate_names[1], urls[1], 3, 150, 180, 20, 50,
          [320, 240], 40, 8, 20, wc, 1/f, 1, 30, 1)

    g3 = (gate_names[2], urls[2], 4, 125, 120, 40, 2000,
          [320, 240], 45, 4, 6, wc, 1/f, 1, 10, 2)

    g4 = (gate_names[3], urls[3], 4, 125, 160, 40, 1400,
          [320, 240], 45, 4, 0, wc, 1/f, 1, 30, 3)

    g5 = (gate_names[4], urls[4], 4, 125, 120, 40, 1400,
          [320, 240], 45, 4, 0, wc, 1/f, 1, 20, 4)

    queue_to_xl = Queue()
    gates = [g1, g2, g3, g4, g5]
    #gates = [g1]
    ex_loop = SharedMemory(create=True, size=1)
    ex_loop.buf[0] = True

    p_gates = [Process(target=gate_func, args=(ex_loop ,*g)) for g in gates]
    p_xl = Process(target=excel_func, args=([ex_loop]))
    p_s = [*p_gates, p_xl]

    for p in p_s:
        p.start()
    
    k = 'a'
    while k not in ['quit', 'q', 'exit']:
        k = input()

    ex_loop.buf[0] = False
    
    up_down.shm.unlink()
    up_down.shm.close()
    queue_to_xl.cancel_join_thread()
    queue_to_xl.close()
    for p in p_s:
        p.join()
