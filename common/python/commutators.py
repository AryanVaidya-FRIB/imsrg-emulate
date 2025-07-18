#!/usr/bin/env python

#------------------------------------------------------------------------------
# commutators.py
#
# author:   A. Vaidya
# version:  1.0
# date:     Nov 26, 2024
# 
# tested with Python v3.10
# 
# Contains general IMSRG(2) commutator. 
# Needs user_data to be defined when called, including bases, occupation bases
# and reference state.
#
#------------------------------------------------------------------------------

import numpy as np
from numpy import array, dot, diag, reshape, transpose
from math import factorial
from basis import ph_transform_2B, inverse_ph_transform_2B

#-----------------------------------------------------------------------------------
# commutator of matrices
#-----------------------------------------------------------------------------------
def commutator(a,b):
  return dot(a,b) - dot(b,a)

# -----------------------------------------------------------------------------
# Commutator of two operators truncated to two-body order, using C = [A,B]
# Included elements are labeled [Operator]_[n-body] 
# Ex. A_1 is the 1-body piece of A
# -----------------------------------------------------------------------------

def commutator_2b(A1, A2, B1, B2, user_data):

  dim1B     = user_data["dim1B"]
  holes     = user_data["holes"]
  particles = user_data["particles"]
  bas2B     = user_data["bas2B"]
  idx2B     = user_data["idx2B"]
  basph2B   = user_data["basph2B"]
  idxph2B   = user_data["idxph2B"]
  occB_2B   = user_data["occB_2B"]
  occC_2B   = user_data["occC_2B"]
  occphA_2B = user_data["occphA_2B"]

  #############################        
  # zero-body flow equation
  C0 = 0.0

  for i in holes:
    for a in particles:
      C0 += A1[i,a] * B1[a,i] - A1[a,i] * B1[i,a]

  for i in holes:
    for j in holes:
      for a in particles:
        for b in particles:
          C0 += 0.25 * (A2[idx2B[(i,j)], idx2B[(a,b)]] * B2[idx2B[(a,b)], idx2B[(i,j)]]
                         -B2[idx2B[(i,j)], idx2B[(a,b)]] * A2[idx2B[(a,b)], idx2B[(i,j)]])


  #############################        
  # one-body flow equation  
  C1  = np.zeros_like(B1)

  # 1B - 1B
  C1 += commutator(A1, B1)

  # 1B - 2B
  for p in range(dim1B):
    for q in range(dim1B):
      for i in holes:
        for a in particles:
          C1[p,q] += (
            A1[i,a] * B2[idx2B[(a, p)], idx2B[(i, q)]] 
            - A1[a,i] * B2[idx2B[(i, p)], idx2B[(a, q)]] 
            - B1[i,a] * A2[idx2B[(a, p)], idx2B[(i, q)]] 
            + B1[a,i] * A2[idx2B[(i, p)], idx2B[(a, q)]]
          )

  # 2B - 2B
  # n_a n_b nn_c + nn_a nn_b n_c = n_a n_b + (1 - n_a - n_b) * n_c
  crossterm_2B_1 = dot(A2, dot(occB_2B, B2))
  crossterm_2B_2 = dot(B2, dot(occB_2B, A2))
  for p in range(dim1B):
    for q in range(dim1B):
      for i in holes:
        C1[p,q] += 0.5*(
          crossterm_2B_1[idx2B[(i,p)], idx2B[(i,q)]] 
          - crossterm_2B_2[idx2B[(i,p)], idx2B[(i,q)]]
        )

  crossterm_2B_1 = dot(A2, dot(occC_2B, B2))
  crossterm_2B_2 = dot(B2, dot(occC_2B, A2))
  for p in range(dim1B):
    for q in range(dim1B):
      for r in range(dim1B):
        C1[p,q] += 0.5*(
          crossterm_2B_1[idx2B[(r,p)], idx2B[(r,q)]] 
          - crossterm_2B_2[idx2B[(r,p)], idx2B[(r,q)]] 
        )


  #############################        
  # two-body flow equation  
  C2 = np.zeros_like(B2)

  # 1B - 2B
  for p in range(dim1B):
    for q in range(dim1B):
      for r in range(dim1B):
        for s in range(dim1B):
          for t in range(dim1B):
            C2[idx2B[(p,q)],idx2B[(r,s)]] += (
              A1[p,t] * B2[idx2B[(t,q)],idx2B[(r,s)]] 
              + A1[q,t] * B2[idx2B[(p,t)],idx2B[(r,s)]] 
              - A1[t,r] * B2[idx2B[(p,q)],idx2B[(t,s)]] 
              - A1[t,s] * B2[idx2B[(p,q)],idx2B[(r,t)]]
              - B1[p,t] * A2[idx2B[(t,q)],idx2B[(r,s)]] 
              - B1[q,t] * A2[idx2B[(p,t)],idx2B[(r,s)]] 
              + B1[t,r] * A2[idx2B[(p,q)],idx2B[(t,s)]] 
              + B1[t,s] * A2[idx2B[(p,q)],idx2B[(r,t)]]
            )

  
  # 2B - 2B - particle and hole ladders
  # eta2B.occB.Gamma
  crossterm_2B_1 = dot(A2, dot(occB_2B, B2))
  crossterm_2B_2 = dot(B2, dot(occB_2B, A2))

  C2 += 0.5 * (crossterm_2B_1 - crossterm_2B_2)

  # 2B - 2B - particle-hole chain
  
  # transform matrices to particle-hole representation and calculate 
  # eta2B_ph.occA_ph.Gamma_ph
  A2_ph = ph_transform_2B(A2, bas2B, idx2B, basph2B, idxph2B)
  B2_ph = ph_transform_2B(B2, bas2B, idx2B, basph2B, idxph2B)

  crossterm_ph = dot(A2_ph, dot(occphA_2B, B2_ph))

  # transform back to standard representation
  crossterm_2B    = inverse_ph_transform_2B(crossterm_ph, bas2B, idx2B, basph2B, idxph2B)

  # commutator / antisymmetrization
  work = np.zeros_like(crossterm_2B)
  for i1, (i,j) in enumerate(bas2B):
    for i2, (k,l) in enumerate(bas2B):
      work[i1, i2] -= (
        crossterm_2B[i1, i2] 
        - crossterm_2B[idx2B[(j,i)], i2] 
        - crossterm_2B[i1, idx2B[(l,k)]] 
        + crossterm_2B[idx2B[(j,i)], idx2B[(l,k)]]
      )
  crossterm_2B = work

  C2 += crossterm_2B


  return C0, C1, C2

# -----------------------------------------------------------------------------
# BCH for Matrix Transformations of form 
# exp(Operator)Hamiltonian exp(-Operator)
# -----------------------------------------------------------------------------
def matrix_similarity_transform(Operator, Hamiltonian, order):
  dim = Hamiltonian.shape[0]
  Hout = np.zeros((dim,dim))
  for k in range(order):
    temp_H = Hamiltonian
    for _ in range(k):
      temp_H = commutator(Operator, temp_H)
    
    if abs(np.linalg.norm(temp_H)/factorial(k))< 1e-10 and k>6:
      break
    Hout += temp_H/factorial(k)
    print(Hout)

  return Hout

# -----------------------------------------------------------------------------
# BCH for two operators truncated to 2-body contributions
# with form exp(OperatorA) exp(OperatorB)
# -----------------------------------------------------------------------------
def BCH(OperatorA_1B, OperatorA_2B, OperatorB_1B, OperatorB_2B, user_data):
    output_1B = OperatorA_1B + OperatorB_1B
    output_2B = OperatorA_2B + OperatorB_2B

    term_is_big = True

    if term_is_big:
      # 1st order terms
      _, comm1B, comm2B = commutator_2b(OperatorA_1B, OperatorA_2B, OperatorB_1B, OperatorB_2B, user_data) #[X,Y]
      output_1B += comm1B/2
      output_2B += comm2B/2
      check = np.linalg.norm((comm1B/2),ord='fro')+np.linalg.norm((comm2B/2),ord='fro')
      if abs(check) < 1e-5:
        term_is_big = False

    """

    if term_is_big:
      # 2nd order terms
      _, comm1B_A, comm2B_A = commutator_2b(OperatorA_1B, OperatorA_2B, comm1B, comm2B, user_data) #[X,[X,Y]]
      _, comm1B_B, comm2B_B = commutator_2b(OperatorB_1B, OperatorB_2B, comm1B, comm2B, user_data) #[Y,[X,Y]]
      output_1B += (comm1B_A-comm1B_B)/12
      output_2B += (comm2B_A-comm2B_B)/12
      check = np.linalg.norm(((comm1B_A-comm1B_B)/12),ord='fro')+np.linalg.norm(((comm2B_A-comm2B_B)/12),ord='fro')
      if abs(check) < 1e-5:
        term_is_big = False

    if term_is_big:
      # 3rd order term
      _, comm1B_BA, comm2B_BA = commutator_2b(OperatorB_1B, OperatorB_2B, comm1B_A, comm2B_A, user_data) #[Y,[X,[X,Y]]]
      
      output_1B += (comm1B_BA) / 24
      output_2B += (comm2B_BA) / 24
      check = np.linalg.norm((comm1B_BA/24),ord='fro')+np.linalg.norm((comm2B_BA/24),ord='fro')
      if abs(check) < 1e-5:
        term_is_big = False

    if term_is_big:
      # 4th order auxiliary terms
      _, comm1B_AB, comm2B_AB = commutator_2b(OperatorA_1B, OperatorA_2B, comm1B_B, comm2B_B, user_data) #[X,[Y,[X,Y]]]
      _, comm1B_AA, comm2B_AA = commutator_2b(OperatorA_1B, OperatorA_2B, comm1B_A, comm2B_A, user_data) #[X,[X,[X,Y]]]
      _, comm1B_BB, comm2B_BB = commutator_2b(OperatorB_1B, OperatorB_2B, comm1B_B, comm2B_B, user_data) #[Y,[Y,[X,Y]]]
      # 4th order terms
      _, comm1B_AAA, comm2B_AAA = commutator_2b(OperatorA_1B, OperatorA_2B, comm1B_AA, comm2B_AA, user_data) #[X,[X,[X,[X,Y]]]]
      _, comm1B_BBB, comm2B_BBB = commutator_2b(OperatorB_1B, OperatorB_2B, comm1B_BB, comm2B_BB, user_data) #[Y,[Y,[Y,[X,Y]]]]
      _, comm1B_ABB, comm2B_ABB = commutator_2b(OperatorA_1B, OperatorA_2B, comm1B_BB, comm2B_BB, user_data) #[X,[Y,[Y,[X,Y]]]]
      _, comm1B_BAA, comm2B_BAA = commutator_2b(OperatorB_1B, OperatorB_2B, comm1B_AA, comm2B_AA, user_data) #[Y,[X,[X,[X,Y]]]]
      _, comm1B_BAB, comm2B_BAB = commutator_2b(OperatorB_1B, OperatorB_2B, comm1B_AB, comm2B_AB, user_data) #[Y,[X,[Y,[X,Y]]]]
      _, comm1B_ABA, comm2B_ABA = commutator_2b(OperatorA_1B, OperatorA_2B, comm1B_BA, comm2B_BA, user_data) #[X,[Y,[X,[X,Y]]]]
      # X,X,X-Y,Y,Y
      val_1B = -(comm1B_AAA-comm1B_BBB)/720
      val_2B = -(comm2B_AAA-comm2B_BBB)/720
      # Y,X,X-X,Y,Y
      val_1B += (comm1B_BAA-comm1B_ABB)/360
      val_2B += (comm2B_BAA-comm2B_ABB)/360
      # Y,X,Y-X,Y,X
      val_1B += (comm1B_BAB-comm1B_ABA)/120
      val_2B += (comm2B_BAB-comm2B_ABA)/120

      check = np.linalg.norm(val_1B,ord='fro')+np.linalg.norm(val_2B,ord='fro')
      if abs(check) < 1e-5:
        term_is_big = False

    if term_is_big:
      # Fifth order term
      _, comm1B_ABAB, comm2B_ABAB = commutator_2b(OperatorA_1B, OperatorA_2B, comm1B_BAB, comm2B_BAB, user_data)
      output_1B += comm1B_ABAB/240
      output_2B += comm2B_ABAB/240

    """
    return output_1B, output_2B

# -----------------------------------------------------------------------------
# BCH Transformation for IMSRG Transformations truncated at 2-body contributions
# with form exp(Operator)Hamiltonian exp(-Operator)
# -----------------------------------------------------------------------------
def similarity_transform(Operator1B, Operator2B, E, f, Gamma, user_data):
    E_s = 0
    f_s = np.zeros(f.shape)
    Gamma_s = np.zeros(Gamma.shape)

    BCH_Order = user_data["order"]
    for k in range(BCH_Order):
      temp_E = E
      temp_f = f
      temp_Gamma = Gamma
      for _ in range(k):
        temp_E, temp_f, temp_Gamma = commutator_2b(Operator1B, Operator2B, temp_f, temp_Gamma, user_data)

      if abs(temp_E/factorial(k)) < 1E-10 and k > 6: 
        break
      E_s += temp_E/factorial(k)
      f_s += temp_f/factorial(k)
      Gamma_s += temp_Gamma/factorial(k)

    return E_s, f_s, Gamma_s