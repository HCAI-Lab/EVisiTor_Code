;;; Task 1: OPEN FILE
(setq subtask1_1_list '((Goto "File Tab") (Select "File Tab") (end)))
(setq subtask1_2_list '((Goto "Open") (Select "Open") (end)))
(setq subtask1_3_list '((Goto "normalization.xlsx") (Select "normalization.xlsx") (endsub)))

;;; Task 2: SAVE AS
(setq subtask2_1_list '((Goto "File Tab") (Select "File Tab") (end)))
(setq subtask2_2_list '((Goto "Save as") (Select "Save as") (end)))
(setq subtask2_3_list '((Goto "file name area") (Select "file name area") (end)))
(setq subtask2_4_list '((Type "subject") (Press "enter") (end)))
(setq subtask2_5_list '((Goto "Save") (Select "Save") (endsub)))

;;; Task 3: FILL FREQUENCY COLUMN B7-B11
(setq subtask3_1_list '((Goto "b7") (Select "b7") (end)))
(setq subtask3_2_list '((Type "=(c7*b13)/100") (Press "enter") (end)))
(setq subtask3_3_list '((Goto "b8") (Select "b8") (end)))
(setq subtask3_4_list '((Type "=(c8*b13)/100") (Press "enter") (end)))
(setq subtask3_5_list '((Goto "b9") (Select "b9") (end)))
(setq subtask3_6_list '((Type "=(c9*b13)/100") (Press "enter") (end)))
(setq subtask3_7_list '((Goto "b10") (Select "b10") (end)))
(setq subtask3_8_list '((Type "=(c10*b13)/100") (Press "enter") (end)))
(setq subtask3_9_list '((Goto "b11") (Select "b11") (end)))
(setq subtask3_10_list '((Type "=(c11*b13)/100") (Press "enter") (endsub)))

;;; Task 4: TOTAL FREQUENCY IN B14
(setq subtask4_1_list '((Goto "b14") (Select "b14") (end)))
(setq subtask4_2_list '((Type "=sum(b2:b11)") (Press "enter") (endsub)))

;;; Task 5: FILL NORMALIZATION COLUMN C2-C6
(setq subtask5_1_list '((Goto "c2") (Select "c2") (end)))
(setq subtask5_2_list '((Type "=(b2*100)/b13") (Press "enter") (end)))
(setq subtask5_3_list '((Goto "c3") (Select "c3") (end)))
(setq subtask5_4_list '((Type "=(b3*100)/b13") (Press "enter") (end)))
(setq subtask5_5_list '((Goto "c4") (Select "c4") (end)))
(setq subtask5_6_list '((Type "=(b4*100)/b13") (Press "enter") (end)))
(setq subtask5_7_list '((Goto "c5") (Select "c5") (end)))
(setq subtask5_8_list '((Type "=(b5*100)/b13") (Press "enter") (end)))
(setq subtask5_9_list '((Goto "c6") (Select "c6") (end)))
(setq subtask5_10_list '((Type "=(b6*100)/b13") (Press "enter") (endsub)))

;;; Task 6: TOTAL NORMALIZATION IN C14
(setq subtask6_1_list '((Goto "c14") (Select "c14") (end)))
(setq subtask6_2_list '((Type "=sum(c2:c11)") (Press "enter") (endsub)))

;;; Task 7: FILL LENGTH COLUMN D2-D11
(setq subtask7_1_list '((Goto "d2") (Select "d2") (end)))
(setq subtask7_2_list '((Type "=len(a2)") (Press "enter") (end)))
(setq subtask7_3_list '((Goto "d3") (Select "d3") (end)))
(setq subtask7_4_list '((Type "=len(a3)") (Press "enter") (end)))
(setq subtask7_5_list '((Goto "d4") (Select "d4") (end)))
(setq subtask7_6_list '((Type "=len(a4)") (Press "enter") (end)))
(setq subtask7_7_list '((Goto "d5") (Select "d5") (end)))
(setq subtask7_8_list '((Type "=len(a5)") (Press "enter") (end)))
(setq subtask7_9_list '((Goto "d6") (Select "d6") (end)))
(setq subtask7_10_list '((Type "=len(a6)") (Press "enter") (end)))
(setq subtask7_11_list '((Goto "d7") (Select "d7") (end)))
(setq subtask7_12_list '((Type "=len(a7)") (Press "enter") (end)))
(setq subtask7_13_list '((Goto "d8") (Select "d8") (end)))
(setq subtask7_14_list '((Type "=len(a8)") (Press "enter") (end)))
(setq subtask7_15_list '((Goto "d9") (Select "d9") (end)))
(setq subtask7_16_list '((Type "=len(a9)") (Press "enter") (end)))
(setq subtask7_17_list '((Goto "d10") (Select "d10") (end)))
(setq subtask7_18_list '((Type "=len(a10)") (Press "enter") (end)))
(setq subtask7_19_list '((Goto "d11") (Select "d11") (end)))
(setq subtask7_20_list '((Type "=len(a11)") (Press "enter") (endsub)))

;;; Task 8: TOTAL LENGTH IN D14
(setq subtask8_1_list '((Goto "d14") (Select "d14") (end)))
(setq subtask8_2_list '((Type "=sum(d2:d11)") (Press "enter") (endsub)))

;;; Task 9: FILL TYPED-CHARS COLUMN E2-E11
(setq subtask9_1_list '((Goto "e2") (Select "e2") (end)))
(setq subtask9_2_list '((Type "=d2*b2") (Press "enter") (end)))
(setq subtask9_3_list '((Goto "e3") (Select "e3") (end)))
(setq subtask9_4_list '((Type "=d3*b3") (Press "enter") (end)))
(setq subtask9_5_list '((Goto "e4") (Select "e4") (end)))
(setq subtask9_6_list '((Type "=d4*b4") (Press "enter") (end)))
(setq subtask9_7_list '((Goto "e5") (Select "e5") (end)))
(setq subtask9_8_list '((Type "=d5*b5") (Press "enter") (end)))
(setq subtask9_9_list '((Goto "e6") (Select "e6") (end)))
(setq subtask9_10_list '((Type "=d6*b6") (Press "enter") (end)))
(setq subtask9_11_list '((Goto "e7") (Select "e7") (end)))
(setq subtask9_12_list '((Type "=d7*b7") (Press "enter") (end)))
(setq subtask9_13_list '((Goto "e8") (Select "e8") (end)))
(setq subtask9_14_list '((Type "=d8*b8") (Press "enter") (end)))
(setq subtask9_15_list '((Goto "e9") (Select "e9") (end)))
(setq subtask9_16_list '((Type "=d9*b9") (Press "enter") (end)))
(setq subtask9_17_list '((Goto "e10") (Select "e10") (end)))
(setq subtask9_18_list '((Type "=d10*b10") (Press "enter") (end)))
(setq subtask9_19_list '((Goto "e11") (Select "e11") (end)))
(setq subtask9_20_list '((Type "=d11*b11") (Press "enter") (endsub)))

;;; Task 10: TOTAL TYPED-CHARS IN E14
(setq subtask10_1_list '((Goto "e14") (Select "e14") (end)))
(setq subtask10_2_list '((Type "=sum(e2:e11)") (Press "enter") (endsub)))

;;; Task 11: INSERT TWO ROWS AT THE TOP
(setq subtask11_1_list '((Goto "Row 1") (Select "Row 1") (end)))
(setq subtask11_2_list '((Goto "Home") (Select "Home") (end)))
(setq subtask11_3_list '((Goto "Cells") (Select "Cells") (end)))
(setq subtask11_4_list '((Goto "Insert") (Select "Insert") (end)))
(setq subtask11_5_list '((Goto "Insert-cell") (Select "Insert-cell") (end)))
(setq subtask11_6_list '((Goto "Row 1") (Select "Row 1") (end)))
(setq subtask11_7_list '((Goto "Home") (Select "Home") (end)))
(setq subtask11_8_list '((Goto "Cells") (Select "Cells") (end)))
(setq subtask11_9_list '((Goto "Insert") (Select "Insert") (end)))
(setq subtask11_10_list '((Goto "Insert-cell") (Select "Insert-cell") (endsub)))

;;; Task 12: ENTER A NAME IN A1
(setq subtask12_1_list '((Goto "A1") (Select "A1") (end)))
(setq subtask12_2_list '((Type "subject") (Press "enter") (endsub)))

;;; Task 13: ENTER TODAY'S DATE IN A2
(setq subtask13_1_list '((Goto "A2") (Select "A2") (end)))
(setq subtask13_2_list '((Type "=today()") (Press "enter") (endsub)))

;;; Task 14: RESAVE WITH A NEW NAME
(setq subtask14_1_list '((Goto "File Tab") (Select "File Tab") (end)))
(setq subtask14_2_list '((Goto "Save") (Select "Save") (end)))
(setq subtask14_3_list '((Goto "file name area") (Select "file name area") (end)))
(setq subtask14_4_list '((Type "normalization-subject") (Press "enter") (endsub)))
