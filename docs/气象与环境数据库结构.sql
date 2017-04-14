drop table if exists device_list;

/*==============================================================*/
/* Table: device_list                                           */
/*==============================================================*/
create table device_sens_list
(
   dev_id               int not null,
   dev_idno             int,
   dev_name             varchar(20),
   dev_desc             varchar(20),
   dev_type             int,
   dev_cycle            int,
   dev_verf             varchar(0),
   dev_vers             varchar(0),
   dev_com_id           int,
   dev_com_type         int,
   dev_com_baud         int,
   dev_com_bit          int,
   dev_com_parity       int,
   dev_com_stop         int,
   dev_ip               int,
   dev_port             int,
   date_create          bigint,
   date_modify          bigint,
   primary key (dev_id)
);





drop table if exists sens_data_001_month_1608;

/*==============================================================*/
/* Table: data_001_month_1608                                   */
/*==============================================================*/
create table sens_data_001_month_1608
(
   dev_id               bigint not null,
   dev_data             decimal(9,6),
   date_create          bigint not null,
   primary key (dev_id, date_create)
);




drop table if exists sens_trend_data_001_day_16;

/*==============================================================*/
/* Table: trend_data_001_day_16                                 */
/*==============================================================*/
create table sens_trend_data_001_day_16
(
   dev_id               int not null,
   dev_data_max         decimal(9,6),
   dev_data_min         decimal(9,6),
   dev_data_avg         decimal(9,6),
   date_create          bigint not null,
   primary key (dev_id, date_create)
);




drop table if exists sens_trend_data_001_month_16;

/*==============================================================*/
/* Table: trend_data_001_month_16                               */
/*==============================================================*/
create table sens_trend_data_001_month_16
(
   dev_id               int not null,
   dev_data_max         decimal(9,6),
   dev_data_min         decimal(9,6),
   dev_data_avg         decimal(9,6),
   date_create          bigint not null,
   primary key (dev_id, date_create)
);
