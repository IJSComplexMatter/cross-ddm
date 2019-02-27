/* 
===================================================================================================
    Cross DDM random triggering and calculation of triggering times.

    Copyright (C) 2019; Matej Arko, Andrej Petelin

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
===================================================================================================
*/

#include <eRCaGuy_Timer2_Counter.h> 

int r1;
int r2;
long i;
long j;
long period;
unsigned long t;
unsigned long t1;
unsigned long t2;
int n;
int pw;
int fps;
long deltat;
long N;
int zero_trigger;
bool triggering;
bool simulation;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);       //Built-in LED is ON while arduino is active, and flashes when the program is done
  digitalWrite(LED_BUILTIN, LOW);
  Serial.begin(115200);               //Baud rate
  DDRD = B00001100;                   //Port register
  randomSeed(1);
  N=100000;                           //total number of frames on each camera
  fps=200;                            //average framerate in Hz, should be no greater than 1/2 of camera's max fps
  period=1000000/fps;                 //period in microseconds
  n=20;                               //number of allowed random trigger times in one period
  deltat=(int)period/(2*n);           //smallest time delay in us; 1/deltat will be the effective framerate
  pw=32;                              //pulse width in microseconds
  triggering=false;
  simulation=false;
  zero_trigger=0;
  i=0;                                //frame count on 1st camera
  j=0;                                //frame count on 2nd camera
  r1=0;                               //random factor between [0,n)
  r2=0;                               //random factor between [0,2)
  t1=0;                               //next calculated time for 1st camera in units of 0.5 us
  t2=0;                               //next calculated time for 2nd camera in units of 0.5 us
  timer2.setup();
}

void loop() {

  //On standby until the starting signal is recieved on the serial port, built-in LED is OFF.
  while(true){
    if(Serial.available()){
      char serialReader=Serial.read();
      if(serialReader == 'T'){
        triggering=true;
        break;
      }
      else if(serialReader == 'S'){
        simulation=true;
        break;
      }
    }
  }

  // TRIGGERING PART
    
  if(triggering){
    
    Serial.end();
    
    //Start of the triggering, built-in LED is ON
    digitalWrite(LED_BUILTIN, HIGH);
    noInterrupts();
    timer2.reset();
      
    while(triggering==true){
    // t is time since the beginning of measurement, count is in steps of 0.5 us
      t=timer2.get_count();
      if (t>min(t1,t2)){
    
        // Pulses on both pins at the same time.
        if(t1==t2 || zero_trigger==0){
          PORTD = B00001100;
          delayMicroseconds(pw);
          PORTD=B00000000;
          r1=random(0,n);
          r2=(random(0,2))*n;
          i++;
          j++;
          t1=(i*period+r1*deltat)*2;
          t2=(j*period+r2*deltat)*2; 
        }
    
        // Pulse on the first pin.
        else if(t1<t2){
          PORTD = B00000100;
          delayMicroseconds(pw);
          PORTD=B00000000;
          r1=random(0,n);
          i++;
          t1=(i*period+r1*deltat)*2;
        }
    
        // Pulse on the second pin.
        else if(t2<t1){
          PORTD = B00001000;
          delayMicroseconds(pw);
          PORTD=B00000000;
          r2=(random(0,2))*n;
          j++;
          t2=(j*period+r2*deltat)*2;
        }
    
        // Term added to reduce the statistical error of the zero delay data.
        if (i==j){
          zero_trigger=random(0,2*n);
          if (zero_trigger==0){
            t2=t1;
            //t2 is set to t1 with a probability of 1/2n
          }
        }       
      } 
    
      //Stopping criteria.
      if(i==N && j==N){
        interrupts();
        triggering=false;
        break;
      }
    }
   
      
    //On standby until reset, built-in LED is blinking
    while(triggering==false){
      digitalWrite(LED_BUILTIN, LOW);    
      delay(200); 
      digitalWrite(LED_BUILTIN, HIGH);
      delay(200);                       
    }
  }

  // SIMULATION PART
  
  else if(simulation){
    
    digitalWrite(LED_BUILTIN, HIGH);
    
    while(simulation==true){
  
      // Pulses on both pins at the same time. (line looks like this: 0 \t time \n)
      if(t1==t2 || zero_trigger==0){
        Serial.print("0");
        Serial.print("\t");
        Serial.print(t1);
        r1=random(0,n);
        r2=(random(0,2))*n;
        i++;
        j++;
        t1=(i*period+r1*deltat);
        t2=(j*period+r2*deltat);
        Serial.print("\n");
      }
  
      // Pulse on the first pin. (line looks like this: 1 \t time \n)
      else if(t1<t2){
        Serial.print("1");
        Serial.print("\t");
        Serial.print(t1);
        r1=random(0,n);
        i++;
        t1=(i*period+r1*deltat);
        Serial.print("\n");
      }
  
      // Pulse on the second pin. (line looks like this: 2 \t time \n)
      else if(t2<t1){
        Serial.print("2");
        Serial.print("\t");
        Serial.print(t2);  
        r2=(random(0,2))*n;
        j++;
        t2=(j*period+r2*deltat);
        Serial.print("\n");
      }
  
      // Term added to reduce the statistical error of the zero delay data.
      if (i==j){
        zero_trigger=random(0,n*2);
        if (zero_trigger==0){
          t2=t1;
        }
      }
       
      //Stopping criteria.  
      if(i==N && j==N){
        simulation=false;
        break;
      }
    }
    
    //On standby until reset, built-in LED is blinking
    while(simulation==false){
      digitalWrite(LED_BUILTIN, LOW);    
      delay(200); 
      digitalWrite(LED_BUILTIN, HIGH);
      delay(200);                       
    } 
       
  }
}
