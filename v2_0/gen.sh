#!/bin/bash

for i in {1..5}
do
    python Traffic_Generator.py -f model/Application_0${i}.info
done