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


int r1;                 // random integer in the interval [0,n)
int r2;                 // integer that is randomly either 0 or n
long i;                 // frame count on 1st camera
long j;                 // frame count on 2nd camera
long period;            // average period between two frames, calculated as 2*n*deltat
unsigned long t;        // time since beggining of triggering in units of 0,5 us
unsigned long t1;       // next calculated time for 1st camera in units of 0.5 us
unsigned long t2;       // next calculated time for 2nd camera in units of 0.5 us
int n;                  // the 'n' parameter
int pw;                 // trigger pulse width
int pws;                // strobe pulse width, 0 for no strobe
int sdelay;             // strobe delay in microseconds
int p1;                 // first delay
int p2;                 // last delay
int P;                  // intersection of trigger and strobe pulse widths
long deltat;            // minimal time delay in microseconds
unsigned long N;        // total frame count
int zero_trigger;       // random integer in the interval [0,2n)       
bool simulation;        // true if only simulation is performed
bool modified_scheme;   // true for the modified scheme from the article


// this is the data needed to control the trigger 13 bytes long
struct triggerData{ 
    byte mode; //triggering mode; 1 byte
    byte triggering_scheme; //basic or modified triggering scheme; 1byte
    unsigned long count; // total number of frames; 4 bytes 
    int deltat;          // time step (minimum time delay) in microseconds; 2 bytes
    int n;              // the n parameter (see CDDM paper); 2 bytes; Note: period is 2*n*deltat
    int twidth;    // trigger signal width in microseconds; 2 bytes
    int swidth;    // strobe signal width in microseconds; 2 bytes 
    int sdelay;    // strobe delay in microseconds; 2 bytes
};

  // and the struct is overlaid on an array to make it easy to receive data from the PC
  // the received data is copied byte by byte into bytes
  //   and can then be used as, e.g. data.mode
union triggerPC {
   triggerData data;
   byte bytes[16];
};

 // this creates a working instance of the Union
 // elements in it are referred to as, e.g. trigger.data.count
triggerPC trigger;


struct timeData{
  byte id;
  unsigned long t;
};

union timePC {
   timeData data;
   byte bytes[5];
};

timePC _time;


void setup() {  
  
  pinMode(LED_BUILTIN, OUTPUT);       //Built-in LED is ON while arduino is active, and flashes when the program is on standby
  digitalWrite(LED_BUILTIN, LOW);
  
  Serial.begin(115200);  //baud rate
  while (!Serial) {
    ; // wait for serial port to connect. Needed for Native USB only
  }
  Serial.println("CDDM Trigger - v1.0");
  
  DDRD = B00011100; //Port register 
  timer2.setup();
  
}


void loop() {

  //STANDBY UNTIL STARTING SIGNAL FROM SERIAL PORT
  while(true){

      // Blinking of LED when arduino is on stand-by
      digitalWrite(LED_BUILTIN, LOW);    
      delay(200); 
      digitalWrite(LED_BUILTIN, HIGH);
      delay(200);   

         
    if(Serial.available()>= 16){ //starting signal is sent
      for (int k = 0; k < 16; k++){
        trigger.bytes[k] = Serial.read();
      }

      // setting triggering mode and scheme

      if (trigger.data.mode == 1){
         simulation = false;
         }      
      else {
         simulation = true;
         }

      if (trigger.data.triggering_scheme == 1){
         modified_scheme = true;
         }     
      else {
         modified_scheme = false;
         }

      // setting the parameters   
      
      N = trigger.data.count;
      deltat = trigger.data.deltat;
      n = trigger.data.n;
      period = (long) deltat*2 *n;
      pw = trigger.data.twidth;
      pws = trigger.data.swidth;
      sdelay = trigger.data.sdelay;

      //no strobe
      if (pws == 0){
        sdelay=0;
      }
    
      if (sdelay == 0){
        p1=0;
        P=min(pw,pws);
        p2=max(pw,pws)-P;
      }

      //checking if the delay exceeds maximum value both for cases sdelay < 0 and sdelay > 0
      
      else if (sdelay < 0){
        if (-sdelay >= min(pws,deltat-pw)){
          sdelay = 0;
          Serial.print("WARNING: Strobe delay exceeds maximum value. Value is reset to 0.");
        }
        p1=-sdelay;
        if (-sdelay + pw <= pws){
          P=pw;
          p2=pws-P+sdelay;
        }
        else if(-sdelay + pw > pws){
          P=pws+sdelay;
          p2=pw-P;
        }
      }
    
      else if (sdelay > 0){
        if (sdelay >= min(pw,deltat-pws)){
          sdelay = 0;
          Serial.print("WARNING: Strobe delay exceeds maximum value. Value is reset to 0.");
        }
        p1=sdelay;
        if (sdelay + pws <= pw){
          P=pws;
          p2=pw-P-sdelay;
        }
        else if(sdelay + pws > pw){
          P=pw-sdelay;
          p2=pws-P;
        }
      }

      //checking that the width p1+P+p2 of the strobe/trigger signal doesnt exceed deltat
    
      int SUM = p1+P+p2; 
      if (SUM >= deltat){
        Serial.print("WARNING: Trigger signal is out of bounds (SUM >= deltat). Parameters reset to defaults. ");
        //DEFAULT VALUES
        pw=32;
        pws=32;
        sdelay=0;
        p1=0;
        P=32;
        p2=0;
        SUM=P;
      }

      //print to serial
      Serial.print("Triggering mode: ");
      Serial.print(trigger.data.triggering_scheme);      
      Serial.print(", N: ");
      Serial.print(N);
      Serial.print(", Delta t (us): ");
      Serial.print(deltat);
      Serial.print(", Period (us): ");
      Serial.print(period);
      Serial.print(", n: ");
      Serial.print(n);
      Serial.print(", trigger width: ");
      Serial.print(pw);
      Serial.print(", strobe width: ");
      Serial.print(pws);
      Serial.print(", strobe delay: ");
      Serial.print(sdelay);
      Serial.print(", triggering scheme: ");
      Serial.print(trigger.data.triggering_scheme);
      Serial.print("\n");  

      break;     
    }    
  }


  // TRIGGERING PART
  

  if (simulation == false){

    randomSeed(1);

    //starting parameters
    zero_trigger=0;
    i=0;                               
    j=0;                                
    r1=0;                               
    r2=0;                               
    t1=0;                               
    t2=0;                              

    //Serial.end();
    // we are calling noInterrupts() later on... so make sure everything was sent.
    delay(10); // pause for 10 ms    
    //Start of the triggering, built-in LED is ON
    digitalWrite(LED_BUILTIN, HIGH);
    noInterrupts();
    timer2.reset();

    while(true){
      t=timer2.get_count();
      if (t>min(t1,t2)){
      
        // PULSES ON BOTH PINS
                                          // EXAMPLE
        if(t1==t2){
          if (sdelay >= 0){               // trigger starts first
            if (sdelay + pws <= pw){      // strobe ends first
              if (p1 == 0){               // simultaneous start
                if (pws > 0){             // no strobe
                  PORTD=B00011100;
                  delayMicroseconds(P);
                }
              }                           
              else{                       // delayed start
                PORTD=B00001100;
                delayMicroseconds(p1);
                PORTD=B00011100;
                delayMicroseconds(P);
              }
              if (p2 == 0){               // simultaneous end
                PORTD=B00000000;
              }
              else{                       
                PORTD=B00001100;          // delayed end
                delayMicroseconds(p2);
                PORTD=B00000000;          
              }
             }
             else{                        // trigger ends first
              if (p1 ==0){                // simultaneous start
                PORTD=B00011100;
                delayMicroseconds(P);
              }
              else{                       //delayed start
                PORTD=B00001100;
                delayMicroseconds(p1);
                PORTD=B00011100;
                delayMicroseconds(P);
              }
              PORTD=B00010000; 
              delayMicroseconds(p2);
              PORTD=B00000000;            
             }         
          }
          
          else{                           // strobe starts first         
            if (-sdelay + pw <= pws){     // trigger ends first
              PORTD=B00010000;
              delayMicroseconds(p1);
              PORTD=B00011100;
              delayMicroseconds(P);
              if (p2 == 0){               // simultaneous end
                PORTD=B00000000;
              }
              else{                       // delayed end
                PORTD=B00010000;
                delayMicroseconds(p2);
                PORTD=B00000000;
              }
             }
             else{                        // strobe ends first
              PORTD=B00010000;
              delayMicroseconds(p1);
              PORTD=B00011100;
              delayMicroseconds(P);
              if (p2 == 0){               // simultaneous end
                PORTD=B00000000;
              }
              else{                       // delayed end
                PORTD=B00001100;
                delayMicroseconds(p2);
                PORTD=B00000000;
              }
             }
          }
          // choosing next random trigger times
          r1=random(0,n);
          r2=(random(0,2))*n;
          i++;
          j++;
          t1=(i*period+r1*deltat)*2;
          t2=(j*period+r2*deltat)*2; 
        }
    
        // PULSE ON FIRST PIN
        
        else if(t1<t2){
          if (sdelay >= 0){
            if (sdelay + pws <= pw){
              if (p1 == 0){
                if (pws > 0){
                  PORTD=B00010100;
                  delayMicroseconds(P);
                }
              }
              else{
                PORTD=B00000100;
                delayMicroseconds(p1);
                PORTD=B00010100;
                delayMicroseconds(P);
              }
              if (p2 ==0){
                PORTD=B00000000;
              }
              else{
                PORTD=B00000100;
                delayMicroseconds(p2);
                PORTD=B00000000;
              }
             }
             else{
              if (p1 == 0){
                PORTD=B00010100;
                delayMicroseconds(P);
              }
              else{
                PORTD=B00000100;
                delayMicroseconds(p1);
                PORTD=B00010100;
                delayMicroseconds(P);
              }
              PORTD=B00010000;
              delayMicroseconds(p2);
              PORTD=B00000000;
             }
          }
          else{          
            if (-sdelay + pw <= pws){
              PORTD=B00010000;
              delayMicroseconds(p1);
              PORTD=B00010100;
              delayMicroseconds(P);
              if (p2 == 0){
                PORTD=B00000000;
              }
              else{
                PORTD=B00010000;
                delayMicroseconds(p2);
                PORTD=B00000000;
              }
             }
             else{
              PORTD=B00010000;
              delayMicroseconds(p1);
              PORTD=B00010100;
              delayMicroseconds(P);
              if (p2 == 0){
                PORTD=B00000000;
              }
              else{
                PORTD=B00000100;
                delayMicroseconds(p2);
                PORTD=B00000000;
              }
             }
          }
          // choosing the next random trigger time on 1st camera
          r1=random(0,n);
          i++;
          t1=(i*period+r1*deltat)*2;
        }
    
        //PULSE ON SECOND PIN
        
        else if(t2<t1){
          if (sdelay >= 0){
            if (sdelay + pws <= pw){
              if (p1 == 0){
                if (pws > 0){
                  PORTD=B00011000;
                  delayMicroseconds(P);
                }
              }
              else{
                PORTD=B00001000;
                delayMicroseconds(p1);
                PORTD=B00011000;
                delayMicroseconds(P);
              }
              if (p2 == 0){
                PORTD=B00000000;
              }
              else{
                PORTD=B00001000;
                delayMicroseconds(p2);
                PORTD=B00000000;
              }
             }
             else{
              if (p1 == 0){
                PORTD=B00011000;
                delayMicroseconds(P);
              }
              else{
                PORTD=B00001000;
                delayMicroseconds(p1);
                PORTD=B00011000;
                delayMicroseconds(P);
              }
              PORTD=B00010000;
              delayMicroseconds(p2);
              PORTD=B00000000;
             }
          }
          else{          
            if (-sdelay + pw <= pws){
              PORTD=B00010000;
              delayMicroseconds(p1);
              PORTD=B00011000;
              delayMicroseconds(P);
              if (p2 == 0){
                PORTD=B00000000;
              }
              else{
                PORTD=B00010000;
                delayMicroseconds(p2);
                PORTD=B00000000;
              }
             }
             else{
              PORTD=B00010000;
              delayMicroseconds(p1);
              PORTD=B00011000;
              delayMicroseconds(P);
              if (p2 == 0){
                PORTD=B00000000;
              }
              else{
              PORTD=B00001000;
              delayMicroseconds(p2);
              PORTD=B00000000;
              }
             }
          }
          // choosing the next random trigger time on 12nd camera
          r2=(random(0,2))*n;
          j++;
          t2=(j*period+r2*deltat)*2;
        }
      
      
       // Term added to reduce the statistical error of the zero delay data.
       if (i==j){
         zero_trigger=random(0,2*n);
          if ((zero_trigger==0) && (modified_scheme == true)){
            t2=t1;
            //t2 is set to t1 with a probability of 1/2n
          }
        }       
      }
    
      //Stopping criteria.
      if(i==N && j==N){
        interrupts();
        break;
      }
    }
    
  }

  
  // SIMULATION PART

  
  if(simulation == true){ 
    randomSeed(1);

    zero_trigger=0;
    i=0;                                
    j=0;                               
    r1=0;                               
    r2=0;                               
    t1=0;                              
    t2=0;                               

      
    digitalWrite(LED_BUILTIN, HIGH);
    
    while(true){
  
      // Pulses on both pins at the same time. (line looks like this: 0 \t time \n)
      if(t1==t2){
        _time.data.id = 0;
        _time.data.t = t1;
        Serial.write(_time.bytes, 5);
        r1=random(0,n);
        r2=(random(0,2))*n;
        i++;
        j++;
        t1=(i*period+r1*deltat);
        t2=(j*period+r2*deltat);
      }
  
      // Pulse on the first pin. (line looks like this: 1 \t time \n)
      else if(t1<t2){
        _time.data.id = 1;
        _time.data.t = t1;
        Serial.write(_time.bytes, 5);
        r1=random(0,n);
        i++;
        t1=(i*period+r1*deltat);
      }
  
      // Pulse on the second pin. (line looks like this: 2 \t time \n)
      else if(t2<t1){
        _time.data.id = 2;
        _time.data.t = t2;
        Serial.write(_time.bytes, 5); 
        r2=(random(0,2))*n;
        j++;
        t2=(j*period+r2*deltat);
      }

      
      //Term added to reduce the statistical error of the zero delay data.
      if (i==j){
        zero_trigger=random(0,n*2);
        if ((zero_trigger==0) && (modified_scheme == true)){
          t2=t1;
        }
      }
       
      //Stopping criteria.  
      if(i==N && j==N){
        break;
      }
    }
    
    //On standby until reset, built-in LED is blinking
       
  }
  
}
