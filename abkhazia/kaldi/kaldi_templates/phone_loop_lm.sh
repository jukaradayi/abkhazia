#!/bin/bash -u

# Copyright 2015  Thomas Schatz

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# THIS CODE IS PROVIDED *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY IMPLIED
# WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
# MERCHANTABLITY OR NON-INFRINGEMENT.
# See the Apache 2 License for the specific language governing permissions and
# limitations under the License.


###### Parameters ######
# directory generated by phone_loop_lm.py containing all the info about the desired lm
in_dir=data/local/phone_loop
# output directory
out_dir=data/phone_loop
# tmp directory
tmp_dir=data/local/phone_loop_tmp
# log file
log=data/prepare_phone_loop.log
# should be set appropriately depending on whether the
# language model produced is destined to be used with an
# acoustic model trained with or without word position
# dependent variants of the phones
word_position_dependent=true

###### Recipe ######
[ -f cmd.sh ] && source ./cmd.sh \
  || echo "cmd.sh not found. Jobs may not execute properly."

. path.sh || { echo "Cannot source path.sh"; exit 1; }

# First need to do a prepare_lang in the desired folder to get to use the "phone" lexicon
# irrespective of what was used as a lexicon in training.
# If there is a prepare_lang.sh in the local folder we use it otherwise we fall back
# to the original utils/prepare_lang.sh (some slight customizations of the script are
# sometimes necessary, for example to decode with a phone loop language model when word
# position dependent phone variants have been trained).
if [ -f local/prepare_lang.sh ]; then
  prepare_lang_exe=local/prepare_lang.sh
else
  prepare_lang_exe=utils/prepare_lang.sh
fi

$prepare_lang_exe --position-dependent-phones $word_position_dependent \
  $in_dir "<unk>" $tmp_dir $out_dir \
  >& $log
# here we could use a different silence_prob 
# I think however that --position-dependent-phones has to be the same
# as what was used for training (as well as the phones.txt, extra_questions.txt
# and nonsilence_phones.txt, otherwise the mapping between phones and acoustic state
# in the trained model will be lost

# then compile the text format FST to binary format used by kaldi in utils/mkgraph.sh
fstcompile --isymbols=$out_dir/words.txt --osymbols=$out_dir/words.txt --keep_isymbols=false \
--keep_osymbols=false $in_dir/G.txt > $out_dir/G.fst

