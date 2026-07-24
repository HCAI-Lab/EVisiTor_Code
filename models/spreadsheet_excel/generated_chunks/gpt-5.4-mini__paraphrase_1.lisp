;;; Task 1: OPEN FILE
(setq subtask1_1_list '((Goto "File tab") (Select "File tab") (end)))
(setq subtask1_2_list '((Goto "Open") (Select "Open") (end)))
(setq subtask1_3_list '((Goto "normalization.xlsx") (Select "normalization.xlsx") (endsub)))

;;; Task 2: SAVE AS
(setq subtask2_1_list '((Goto "File tab") (Select "File tab") (end)))
(setq subtask2_2_list '((Goto "Save as") (Select "Save as") (end)))
(setq subtask2_3_list '((Goto "file-name input") (Select "file-name input") (end)))
(setq subtask2_4_list '((Type "subject") (end)))
(setq subtask2_5_list '((Goto "Save") (Select "Save") (endsub)))

;;; Task 3: FILL FREQUENCY COLUMN B7-B11
(setq subtask3_1_list '((Goto "B7") (Select "B7") (end)))
(setq subtask3_2_list '((Type "=(C7*B13)/100") (Press "enter") (end)))
(setq subtask3_3_list '((Goto "B8") (Select "B8") (end)))
(setq subtask3_4_list '((Type "=(C8*B13)/100") (Press "enter") (end)))
(setq subtask3_5_list '((Goto "B9") (Select "B9") (end)))
(setq subtask3_6_list '((Type "=(C9*B13)/100") (Press "enter") (end)))
(setq subtask3_7_list '((Goto "B10") (Select "B10") (end)))
(setq subtask3_8_list '((Type "=(C10*B13)/100") (Press "enter") (end)))
(setq subtask3_9_list '((Goto "B11") (Select "B11") (end)))
(setq subtask3_10_list '((Type "=(C11*B13)/100") (Press "enter") (endsub)))

;;; Task 4: TOTAL FREQUENCY IN B14
(setq subtask4_1_list '((Goto "B14") (Select "B14") (end)))
(setq subtask4_2_list '((Type "=sum(b2:b11)") (Press "enter") (endsub)))

;;; Task 5: FILL NORMALIZATION COLUMN C2-C6
(setq subtask5_1_list '((Goto "C2") (Select "C2") (end)))
(setq subtask5_2_list '((Type "=(B2*100)/b13") (Press "enter") (end)))
(setq subtask5_3_list '((Goto "C3") (Select "C3") (end)))
(setq subtask5_4_list '((Type "=(B3*100)/b13") (Press "enter") (end)))
(setq subtask5_5_list '((Goto "C4") (Select "C4") (end)))
(setq subtask5_6_list '((Type "=(B4*100)/b13") (Press "enter") (end)))
(setq subtask5_7_list '((Goto "C5") (Select "C5") (end)))
(setq subtask5_8_list '((Type "=(B5*100)/b13") (Press "enter") (end)))
(setq subtask5_9_list '((Goto "C6") (Select "C6") (end)))
(setq subtask5_10_list '((Type "=(B6*100)/b13") (Press "enter") (endsub)))

;;; Task 6: TOTAL NORMALIZATION IN C14
(setq subtask6_1_list '((Goto "C14") (Select "C14") (end)))
(setq subtask6_2_list '((Type "=sum(c2:c11)") (Press "enter") (endsub)))

;;; Task 7: FILL LENGTH COLUMN D2-D11
(setq subtask7_1_list '((Goto "D2") (Select "D2") (end)))
(setq subtask7_2_list '((Type "=len(a2)") (Press "enter") (end)))
(setq subtask7_3_list '((Goto "D3") (Select "D3") (end)))
(setq subtask7_4_list '((Type "=len(a3)") (Press "enter") (end)))
(setq subtask7_5_list '((Goto "D4") (Select "D4") (end)))
(setq subtask7_6_list '((Type "=len(a4)") (Press "enter") (end)))
(setq subtask7_7_list '((Goto "D5") (Select "D5") (end)))
(setq subtask7_8_list '((Type "=len(a5)") (Press "enter") (end)))
(setq subtask7_9_list '((Goto "D6") (Select "D6") (end)))
(setq subtask7_10_list '((Type "=len(a6)") (Press "enter") (end)))
(setq subtask7_11_list '((Goto "D7") (Select "D7") (end)))
(setq subtask7_12_list '((Type "=len(a7)") (Press "enter") (end)))
(setq subtask7_13_list '((Goto "D8") (Select "D8") (end)))
(setq subtask7_14_list '((Type "=len(a8)") (Press "enter") (end)))
(setq subtask7_15_list '((Goto "D9") (Select "D9") (end)))
(setq subtask7_16_list '((Type "=len(a9)") (Press "enter") (end)))
(setq subtask7_17_list '((Goto "D10") (Select "D10") (end)))
(setq subtask7_18_list '((Type "=len(a10)") (Press "enter") (end)))
(setq subtask7_19_list '((Goto "D11") (Select "D11") (end)))
(setq subtask7_20_list '((Type "=len(a11)") (Press "enter") (endsub)))

;;; Task 8: TOTAL LENGTH IN D14
(setq subtask8_1_list '((Goto "D14") (Select "D14") (end)))
(setq subtask8_2_list '((Type "=sum(d2:d11)") (Press "enter") (endsub)))

;;; Task 9: FILL TYPED-CHARS COLUMN E2-E11
(setq subtask9_1_list '((Goto "E2") (Select "E2") (end)))
(setq subtask9_2_list '((Type "=d2*b2") (Press "enter") (end)))
(setq subtask9_3_list '((Goto "E3") (Select "E3") (end)))
(setq subtask9_4_list '((Type "=d3*b3") (Press "enter") (end)))
(setq subtask9_5_list '((Goto "E4") (Select "E4") (end)))
(setq subtask9_6_list '((Type "=d4*b4") (Press "enter") (end)))
(setq subtask9_7_list '((Goto "E5") (Select "E5") (end)))
(setq subtask9_8_list '((Type "=d5*b5") (Press "enter") (end)))
(setq subtask9_9_list '((Goto "E6") (Select "E6") (end)))
(setq subtask9_10_list '((Type "=d6*b6") (Press "enter") (end)))
(setq subtask9_11_list '((Goto "E7") (Select "E7") (end)))
(setq subtask9_12_list '((Type "=d7*b7") (Press "enter") (end)))
(setq subtask9_13_list '((Goto "E8") (Select "E8") (end)))
(setq subtask9_14_list '((Type "=d8*b8") (Press "enter") (end)))
(setq subtask9_15_list '((Goto "E9") (Select "E9") (end)))
(setq subtask9_16_list '((Type "=d9*b9") (Press "enter") (end)))
(setq subtask9_17_list '((Goto "E10") (Select "E10") (end)))
(setq subtask9_18_list '((Type "=d10*b10") (Press "enter") (end)))
(setq subtask9_19_list '((Goto "E11") (Select "E11") (end)))
(setq subtask9_20_list '((Type "=d11*b11") (Press "enter") (endsub)))

;;; Task 10: TOTAL TYPED-CHARS IN E14
(setq subtask10_1_list '((Goto "E14") (Select "E14") (end)))
(setq subtask10_2_list '((Type "=sum(e2:e11)") (Press "enter") (endsub)))

;;; Task 11: INSERT TWO ROWS AT THE TOP
(setq subtask11_1_list '((Goto "Row 1") (Select "Row 1") (end)))
(setq subtask11_2_list '((Goto "Home ribbon") (Select "Home ribbon") (end)))
(setq subtask11_3_list '((Goto "Cells group") (Select "Cells group") (end)))
(setq subtask11_4_list '((Goto "Insert") (Select "Insert") (end)))
(setq subtask11_5_list '((Goto "Insert-cell") (Select "Insert-cell") (end)))
(setq subtask11_6_list '((Goto "Row 1") (Select "Row 1") (end)))
(setq subtask11_7_list '((Goto "Home ribbon") (Select "Home ribbon") (end)))
(setq subtask11_8_list '((Goto "Cells group") (Select "Cells group") (end)))
(setq subtask11_9_list '((Goto "Insert") (Select "Insert") (end)))
(setq subtask11_10_list '((Goto "Insert-cell") (Select "Insert-cell") (endsub)))

;;; Task 12: ENTER A NAME IN A1
(setq subtask12_1_list '((Goto "A1") (Select "A1") (end)))
(setq subtask12_2_list '((Type "subject") (Press "enter") (endsub)))

;;; Task 13: ENTER TODAY'S DATE IN A2
(setq subtask13_1_list '((Goto "A2") (Select "A2") (end)))
(setq subtask13_2_list '((Type "=today()") (Press "enter") (endsub)))

;;; Task 14: RESAVE WITH A NEW NAME
(setq subtask14_1_list '((Goto "File tab") (Select "File tab") (end)))
(setq subtask14_2_list '((Goto "Save") (Select "Save") (end)))
(setq subtask14_3_list '((Goto "file-name input") (Select "file-name input") (end)))
(setq subtask14_4_list '((Type "normalization-subject") (Press "enter") (endsub)))
