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

//GLOBAL VARIABLES
int r1;                 // random integer in the interval [0,n)
int r2;                 // integer that is randomly either 0 or n
long i;                 // frame count on 1st camera
long j;                 // frame count on 2nd camera
long period;            // average period between two frames, calculated as 2*n*deltat
unsigned long t1;       // next calculated time for 1st camera
unsigned long t2;       // next calculated time for 2nd camera
unsigned long d1;       // next calculated time sleep before pulse on the 1st camera
unsigned long d2;       // next calculated time sleep before pulse on the 2st camera
int n;                  // the 'n' parameter
int pw;                 // trigger pulse width
int pws;                // strobe pulse width, 0 for no strobe
int sdelay;             // strobe delay in microseconds
int p1;                 // first delay
int p2;                 // last delay
int P;                  // intersection of trigger and strobe pulse widths
int SUM;                // Sum of p1, P and p2
long deltat;            // minimal time delay in microseconds
unsigned long N;        // total frame count
int zero_trigger;       // random integer in the interval [0,2n)       
bool triggering;        // true if only triggering is performed
bool modified_scheme;   // true for the modified scheme from the article
bool modulo;            // true for the modulo t2 instead of random t2

//timer
byte _tccr1a_save; //will be used to backup default settings
byte _tccr1b_save; //will be used to backup default settings
volatile unsigned long _overflow_count;
unsigned long _total_count;
unsigned long t; //timer count with resolution 4us

//Port bytes
byte c1;
byte c2;
byte s;
byte b01;
byte b02;
byte b03;
byte b11;
byte b12;
byte b13;
byte b21;
byte b22;
byte b23;


// this is the data needed to control the trigger 17 bytes long
struct triggerData{ 
    byte triggering; //Simulation (0) or triggering (1); 1 byte
    int mode; //Triggering mode: 0 - random t2, 1 - random t2 + zero modification, 2 - modulo t2, 3 - modulo t2 + zero modification.; 2 bytes
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
   byte bytes[17];
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


//16BIT TIMER1 COUNTER

unsigned long get_count()
{
  uint8_t SREG_old = SREG; //back up the AVR Status Register; see example in datasheet on pg. 14, as well as Nick Gammon's "Interrupts" article - http://www.gammon.com.au/forum/?id=11488
  noInterrupts(); //prepare for critical section of code
  uint16_t tcnt1_save = TCNT1; //grab the counter value from Timer1
  boolean flag_save = bitRead(TIFR1,0); //grab the timer1 overflow flag value; see datasheet pg. 160
  if (flag_save) { //if the overflow flag is set
    tcnt1_save = TCNT1; //update variable just saved since the overflow flag could have just tripped between previously saving the TCNT1 value and reading bit 0 of TIFR1.  
    _overflow_count++; //force the overflow count to increment
    TIFR1 |= 0b00000001; //reset Timer1 overflow flag since we just manually incremented above; this prevents execution of Timer1's overflow ISR
  }
  _total_count = _overflow_count*256*256 + tcnt1_save; //get total Timer1 count
  SREG = SREG_old; //use this method instead, to re-enable interrupts if they were enabled before, or to leave them disabled if they were disabled before
  return _total_count;
}

void timer_setup() {
  _overflow_count = 0;
  _total_count = 0;
  
  _tccr1a_save = TCCR1A; //first, backup some values
  _tccr1b_save = TCCR1B; //backup some more values
  
  //set prescalers
  TCCR1B = TCCR1B & 0b11111000 | 0x03; // Resolution is 4 us, SET 0x02, for 0.5 us, counter has a higher resolution, but overflow occurs faster

  //Enable Timer1 overflow interrupt;
  //TIMSK1 |= 0b00000001; //enable Timer1 overflow interrupt. (by making the right-most bit in TIMSK1 a 1)
  TIMSK1 &= 0b11111110; //use this code to DISABLE the Timer1 overflow interrupt, if you ever wish to do so later.
  
  TCCR1A &= 0b11111100; //set WGM11 & WGM10 to 0
  TCCR1B &= 0b11110111; //set WGM12 to 0.
}

void timer_reset()
{
  _overflow_count = 0; //reset overflow counter
  _total_count = 0; //reset total counter
  TCNT1 = 0; //reset Timer1 counter
  TIFR1 |= 0b00000001; //reset Timer1 overflow flag; this prevents an immediate execution of Timer1's overflow ISR
}


//PULSE SHAPE AND PORT EVENTS FUNCTION

int find_shape(){

  // p1 and p2 are 4 where they shoulde be 0!
  // In this case this is due to bad behaviour od delayMicroseconds(0)
  // Additional delay does not change the overall accuracy of triggering times, because they are all shifted the same
  
  if (sdelay < 0){
    
    p1=-sdelay;

    if(-sdelay + pw > pws){
      
      P=pws+sdelay;
      p2=pw-P;
      
      b01=s;
      b02=s|c1|c2;
      b03=c1|c2;
    }
    
    else if (-sdelay + pw < pws){
      
      P=pw;
      p2=pws-P+sdelay;

      b01=s;
      b02=s|c1|c2;
      b03=s;
    }
    
    else if (-sdelay + pw == pws){

      P=pw;
      p2=4;

      b01=s;
      b02=s|c1|c2;
      b03=B00000000;
    }
  }
  
  else if (sdelay > 0){
    
    p1=sdelay;
    
    if(sdelay + pws > pw){
      
      P=pw-sdelay;
      p2=pws-P;
      
      b01=c1|c2;
      b02=s|c1|c2;
      b03=s;
    }
    
    else if (sdelay + pws < pw){
      
      P=pws;
      p2=pw-P-sdelay;
      
      b01=c1|c2;
      b02=s|c1|c2;
      b03=c1|c2;
    }

    else if(sdelay + pws == pw){
      
      P=pws;
      p2=4;
      
      b01=c1|c2;
      b02=s|c1|c2;
      b03=B00000000;
    }
  }

  else if (sdelay == 0){
    
    p1=4;

    if (pws == 0){
      
      P=pw;
      p2=4;

      b01=B00000000;
      b02=c1|c2;
      b03=B00000000;
    }
    
    else if(pws == pw){
      
      P=pw;
      p2=4;
      
      b01=B00000000;
      b02=s|c1|c2;
      b03=B00000000;
    }
    
    else if (pws > pw){
      
      P=pw;
      p2=pws-pw;
      
      b01=B00000000;
      b02=s|c1|c2;
      b03=s;
    }

    else if(pws < pw){
      
      P=pws;
      p2=pw-pws;
      
      b01=B00000000;
      b02=s|c1|c2;
      b03=c1|c2;
    }
  }

  b11 = b01 & (~c2); // turn off camera 2
  b12 = b02 & (~c2);
  b13 = b03 & (~c2);

  b21 = b01 & (~c1); // turn off camera 1
  b22 = b02 & (~c1); 
  b23 = b03 & (~c1);  
}


//PULSE FUNCTION

void pulse(int c){
  switch(c){
    
    case 0: //both cameras
    
      delayMicroseconds(d1);
      PORTD = b01;
      delayMicroseconds(p1);
      PORTD= b02;
      delayMicroseconds(P);
      PORTD= b03;
      delayMicroseconds(p2);
      PORTD=B00000000;         
      break;
      
    case 1: //first camera first   
      delayMicroseconds(d1);
      PORTD = b11;
      delayMicroseconds(p1);
      PORTD= b12;
      delayMicroseconds(P);
      PORTD= b13;
      delayMicroseconds(p2);
      PORTD=B00000000;
      delayMicroseconds(d2);
      PORTD = b21;
      delayMicroseconds(p1);
      PORTD= b22;
      delayMicroseconds(P);
      PORTD= b23;
      delayMicroseconds(p2);
      PORTD=B00000000;      
      break;
      
    case 2: //second camera first
      delayMicroseconds(d2);
      PORTD = b21;
      delayMicroseconds(p1);
      PORTD= b22;
      delayMicroseconds(P);
      PORTD= b23;
      delayMicroseconds(p2);
      PORTD=B00000000;
      delayMicroseconds(d1);
      PORTD = b11;
      delayMicroseconds(p1);
      PORTD= b12;
      delayMicroseconds(P);
      PORTD= b13;
      delayMicroseconds(p2);
      PORTD=B00000000;      
      break;
  }
}


//WRITING TO SERIAL DURING SIMULATION

void write_to_serial(int c){
  
  if (c == 0){
    _time.data.id = 0;
    _time.data.t = i*period+t1;
    Serial.write(_time.bytes, 5);
  }
  
  else if(c == 1){
    _time.data.id = 1;
    _time.data.t = i*period+t1;
    Serial.write(_time.bytes, 5);
    _time.data.id = 2;
    _time.data.t = i*period+t2;
    Serial.write(_time.bytes, 5);
  }
  
  else if(c == 2){
    _time.data.id = 2;
    _time.data.t = i*period+t2;
    Serial.write(_time.bytes, 5);
    _time.data.id = 1;
    _time.data.t = i*period+t1;
    Serial.write(_time.bytes, 5);
  }
}

//SETUP

void setup() {  
  
  pinMode(LED_BUILTIN, OUTPUT);       //Built-in LED is ON while arduino is active, and flashes when the program is on standby
  digitalWrite(LED_BUILTIN, LOW);
  
  Serial.begin(115200);  //baud rate
  while (!Serial) {
    ; // wait for serial port to connect. Needed for Native USB only
  }
  Serial.println("CDDM Trigger - v1.0");
  
  timer_setup();

  c1 = B00000100; // first camera port
  c2 = B00001000; // second camera port
  s = B00010000;  // strobe port

  DDRD = c1|c2|s; //Port register 
}


void loop() {

  //STANDBY UNTIL STARTING SIGNAL FROM SERIAL PORT
  while(true){

      // Blinking of LED when arduino is on stand-by
      digitalWrite(LED_BUILTIN, LOW);    
      delay(100); 
      digitalWrite(LED_BUILTIN, HIGH);
      delay(100);   

    //STARTING PROCEDURE
         
    if(Serial.available()>= 17){ //starting signal is sent
      for (int k = 0; k < 17; k++){
        trigger.bytes[k] = Serial.read();
      }

      // setting triggering

      if (trigger.data.triggering == 1){
         triggering = true;
         }      
      else {
         triggering = false;
         }
         
      if (trigger.data.mode <= 1){
        modulo = false;
      }
      else if(trigger.data.mode <= 3){
        modulo = true;
      }
      else{
        Serial.print("WARNING: Triggering mode should be in [0,3]. Value is reset to 0.");
      }

      if (trigger.data.mode % 2 == 0){
        modified_scheme = false;
      }
      else{
        modified_scheme = true;
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
    
      //checking if the delay exceeds maximum value both for cases sdelay < 0 and sdelay > 0
      
      if (sdelay < 0){
        if (-sdelay >= min(pws,deltat-pw)){
          sdelay = 0;
          Serial.print("WARNING: Strobe delay exceeds maximum value. Value is reset to 0.");
        }
      }
    
      else if (sdelay > 0){
        if (sdelay >= min(pw,deltat-pws)){
          sdelay = 0;
          Serial.print("WARNING: Strobe delay exceeds maximum value. Value is reset to 0.");
        }
      }

      find_shape();

      //checking that the width p1+P+p2 of the strobe/trigger signal doesnt exceed deltat
    
      SUM = p1+P+p2; 
      
      if (SUM >= deltat){
        Serial.print("WARNING: Trigger signal is out of bounds (SUM >= deltat). Parameters reset to defaults. ");
        //DEFAULT VALUES
        pw=32;
        pws=0;
        sdelay=0;     
        p1=0;
        P=32;
        p2=0;
        SUM=P;
      }
      
      //print to serial
      Serial.print("Triggering mode: ");
      Serial.print(trigger.data.mode);      
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
      Serial.print("\n");      
      break;     
    }    
  }


  // TRIGGERING OR SIMULATION PART
  
  randomSeed(1);

  //starting parameters setup
  zero_trigger=0;
  i=0;                                                             
  r1=0;                               
  r2=0;                               
  t1=0;                               
  t2=0;
  d1=0;
  d2=0;  
  int c = 0; //case (both / first,second / second,first)                          
 
  // we are calling noInterrupts() later on... so make sure everything was sent.
  delay(10); // pause for 10 ms    
  //Start of the triggering, built-in LED is ON
  digitalWrite(LED_BUILTIN, HIGH);

  if (triggering == true){
    noInterrupts();
  }

  timer_reset(); //counter is now on zero

  //MAIN LOOP
  
  //====================================================================
  
  while(true){

    if (triggering == true){
      t=get_count()*4; //running counter
    }
    else{
      t=i*period+1;
    }

    if (t >= (i*period)){
      
      //double pulse event      
      
      if (triggering == true){
        pulse(c);        
      }
      else{
        write_to_serial(c);
      }
      i++;

      //calculation part
      
      r1=random(0,n);
      if(modulo == true){
        r2 = (i%2)*n;
      }
      else{
        r2=(random(0,2))*n;
      }
      t1=(r1*deltat);
      t2=(r2*deltat);
      
      zero_trigger=random(0,2*n);
      
      if ((zero_trigger==0) && (modified_scheme == true)){
        //t2 is set to t1 with a probability of 1/2n
        t2=t1;
      }

      //determine case
      
      if (t1==t2){
        c=0;
        d1=t1;
      }
      else if (t1<t2){
        c=1;
        d2=t2-t1-SUM;
        d1=t1;
      }
      else if (t1>t2){
        c=2;
        d1=t1-t2-SUM;
        d2=t2;
      }
      
    }       
  
    //Stopping criteria.
    if(i==N){
      break;
    }
    
  }
  
  //====================================================================    
}


