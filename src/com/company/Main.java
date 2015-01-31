package com.company;

public class Main {

    public static void main(String[] args) {
        int[] sizes = new int[8];
        sizes [0] = 4;
        sizes [1] = 9;
        sizes [2] = 8;
        sizes [3] = 15;
        sizes [4] = 19;
        sizes [5] = 19;
        sizes [6] = -16;
        sizes [7] = 223;

        Sort(sizes);
        System.out.print("The Sorted Array is: ");
        printArrays(sizes);
    }

    public static void printArrays(int[] array ){
        for (int i = 0; i <array.length-1 ; i++) {
            System.out.print(array[i]+",");
        }
        System.out.println(array[array.length-1]);
    }

    public static void Sort (int [] arr)
    {
        int first, temp, j;
        for (int i = arr.length -1; i > 0; i--)
        {

            first = 0;
            for(j = 0; j <= i; j ++)
            {
                if(arr[j] > arr[first])
                    first = j;

            }
            temp = arr[first];
            arr[first] = arr[i];
            arr[i] = temp;
        }

    }

}

